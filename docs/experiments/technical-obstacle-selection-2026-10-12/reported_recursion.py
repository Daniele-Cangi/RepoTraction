from unittest import mock
depth = 0


def func(obj):
    global depth
    depth = depth + 1
    print(depth)
    if depth == 1000:
        raise Exception
    return func(obj.attr)  # Infinite loop


def test_func():
    func(mock.MagicMock())


test_func()
