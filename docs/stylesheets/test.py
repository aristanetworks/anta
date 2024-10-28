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

    pass


t = Test()
t.append(42)
z: list[int] = [42, 43]

reveal_type(t)
reveal_type(z)
