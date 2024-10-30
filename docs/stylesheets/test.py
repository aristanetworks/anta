# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from typing import TypeVar

T = TypeVar("T")


# 3.12 syntax
# class Test[T](list[T]):
class Test(list[T]):
    T = type(int)

    def __getitem__(self, index: int) -> int:
        pass

    def __iter__(self) -> Iterator[int]:
        pass

    def __len__(self) -> int:
        return 42


t = Test()
t.append(42)
z: list[int] = [42, 43]

reveal_type(t)
reveal_type(z)
