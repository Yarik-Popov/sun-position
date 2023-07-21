from sun import ephemeris
import pytest


def test_is_float0():
    assert ephemeris.is_float('-1.0')


def test_is_float1():
    assert ephemeris.is_float('1')


def test_is_float2():
    assert ephemeris.is_float("1.0")


def test_is_float3():
    assert ephemeris.is_float("1")


def test_is_float4():
    assert not ephemeris.is_float("a")


def test_is_float5():
    assert not ephemeris.is_float("1a")


def test_is_float6():
    assert not ephemeris.is_float("a1")


def test_is_float7():
    assert not ephemeris.is_float("1.0a")


def test_is_float8():
    assert not ephemeris.is_float("a1.0")


def test_is_float9():
    assert not ephemeris.is_float("1.a0")


def test_is_valid_time0():
    assert ephemeris.is_valid_time("JD2451545.0")


def test_is_valid_time1():
    assert ephemeris.is_valid_time("JD2451545")


def test_is_valid_time2():
    assert ephemeris.is_valid_time("2020-01-02")


def test_is_valid_time3():
    assert not ephemeris.is_valid_time("2020-01-02 12:00:00")


def test_calculate_step_size0():
    assert ephemeris.calculate_step_size(1, 1, 1) == 0


def test_calculate_step_size1():
    assert ephemeris.calculate_step_size(1, 3, 2) == 2


def test_calculate_step_size2():
    assert ephemeris.calculate_step_size(1, 7, 4) == 2


def test_calculate_step_size3():
    assert ephemeris.calculate_step_size(10, 110, 11) == 10


def test_calculate_step_size4():
    with pytest.raises(ValueError) as _:
        ephemeris.calculate_step_size(1, 1, 0)


def test_calculate_step_size5():
    with pytest.raises(ValueError) as _:
        ephemeris.calculate_step_size(1, 1, -1)


def test_calculate_step_size6():
    with pytest.raises(ValueError) as _:
        ephemeris.calculate_step_size(1, 1, 2)


def test_calculate_step_size7():
    with pytest.raises(ValueError) as _:
        ephemeris.calculate_step_size(3, 1, 3)


def main():
    pass


if __name__ == "__main__":
    main()
