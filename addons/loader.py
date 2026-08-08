import os
import sys
import types
import importlib.util
import traceback

hooks = (
    "on_start",
    "on_frame",
    "on_face_found",
    "on_face_lost",
    "on_draw",
    "on_key",
    "on_stop",
)


class ctx:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        keys = ",".join(sorted(self.__dict__))
        return f"<ctx {keys}>"


class AddonManager:
    def __init__(self, folder=None, log=None):
        self.log = log or (lambda m, c="": None)
        self.folder = folder or os.path.dirname(os.path.abspath(__file__))
        self.addons = []
        self._load_all()

    def _load_all(self):
        if not os.path.isdir(self.folder):
            self.log(f"addons: no folder at {self.folder}")
            return

        for fn in sorted(os.listdir(self.folder)):
            if not fn.endswith(".py") or fn.startswith("_") or fn == "loader.py":
                continue
            path = os.path.join(self.folder, fn)
            try:
                mod = self._load_module(fn[:-3], path)
            except Exception as e:
                self.log(f"addons: failed to load {fn}: {e}")
                traceback.print_exc()
                continue

            if not getattr(mod, "ENABLED", True):
                self.log(f"addons: skipping {fn} (disabled)")
                continue

            mod.NAME = getattr(mod, "NAME", fn[:-3])
            if not any(hasattr(mod, h) for h in hooks):
                self.log(f"addons: skipping {fn} (no hooks)")
                continue

            self.addons.append(mod)
            hooks = [h for h in hooks if hasattr(mod, h)]
            self.log(f"addons: loaded {mod.NAME} [{', '.join(hooks)}]")

        self.log(f"addons: {len(self.addons)} active")

    def _load_module(self, name, path):
        spec = importlib.util.spec_from_file_location(f"tracker_addon_{name}", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod

    def dispatch(self, hook, *args, **kw):
        for mod in self.addons:
            fn = getattr(mod, hook, None)
            if fn is None:
                continue
            try:
                fn(*args, **kw)
            except Exception as e:
                self.log(f"addons: {mod.NAME}.{hook} raised {e}")
                traceback.print_exc()
