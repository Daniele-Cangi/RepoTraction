"""Assessor controls for pytest #15099; run with the pinned target on PYTHONPATH.

Prepared before any development-agent attempt or source search. These assertions
combine the public proxy regression with the target's existing #10644 restoration
invariant. They are not a stand-alone imitation of MonkeyPatch.
"""
import unittest

from _pytest.monkeypatch import MonkeyPatch


class Proxy:
    def __init__(self):
        object.__setattr__(self, "_data", {"flag": False})

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self._data[name] = value


class RestorationAcceptance(unittest.TestCase):
    def test_proxy_restores_original_value(self):
        obj, patch = Proxy(), MonkeyPatch()
        patch.setattr(obj, "flag", True)
        self.assertIs(obj.flag, True)
        patch.undo()
        self.assertIs(obj.flag, False)

    def test_inherited_hook_restores_original_value(self):
        class Child(Proxy):
            pass

        obj, patch = Child(), MonkeyPatch()
        patch.setattr(obj, "flag", True)
        patch.undo()
        self.assertIs(obj.flag, False)

    def test_passthrough_hook_does_not_shadow_inherited_attribute(self):
        class Parent:
            flag = 1

        class Child(Parent):
            def __setattr__(self, name, value):
                object.__setattr__(self, name, value)

        obj, patch = Child(), MonkeyPatch()
        patch.setattr(obj, "flag", 2)
        patch.undo()
        self.assertNotIn("flag", vars(obj))
        Parent.flag = 3
        self.assertEqual(obj.flag, 3)

    def test_mixed_hook_preserves_both_storage_kinds(self):
        class Mixed(Proxy):
            ordinary = 1

            def __setattr__(self, name, value):
                if name == "flag":
                    self._data[name] = value
                else:
                    object.__setattr__(self, name, value)

        obj, patch = Mixed(), MonkeyPatch()
        patch.setattr(obj, "flag", True)
        patch.setattr(obj, "ordinary", 2)
        patch.undo()
        self.assertIs(obj.flag, False)
        self.assertNotIn("ordinary", vars(obj))
        Mixed.ordinary = 3
        self.assertEqual(obj.ordinary, 3)

    def test_nested_changes_restore_in_reverse_order(self):
        obj = Proxy()
        outer, inner = MonkeyPatch(), MonkeyPatch()
        outer.setattr(obj, "flag", "outer")
        inner.setattr(obj, "flag", "inner")
        inner.undo()
        self.assertEqual(obj.flag, "outer")
        outer.undo()
        self.assertIs(obj.flag, False)

    def test_own_value_restores_identity(self):
        class Own:
            pass

        obj, original, patch = Own(), [], MonkeyPatch()
        obj.flag = original
        patch.setattr(obj, "flag", object())
        patch.undo()
        self.assertIs(obj.flag, original)

    def test_property_setter_restores_value(self):
        class Property:
            def __init__(self):
                self._flag = False

            @property
            def flag(self):
                return self._flag

            @flag.setter
            def flag(self, value):
                self._flag = value

        obj, patch = Property(), MonkeyPatch()
        patch.setattr(obj, "flag", True)
        patch.undo()
        self.assertIs(obj.flag, False)
        self.assertNotIn("flag", vars(obj))

    def test_slot_restores_value(self):
        class Slots:
            __slots__ = ("flag",)

        obj, patch = Slots(), MonkeyPatch()
        obj.flag = False
        patch.setattr(obj, "flag", True)
        patch.undo()
        self.assertIs(obj.flag, False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
