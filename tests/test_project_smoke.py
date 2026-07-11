def test_package_exposes_version():
    import one_tone

    assert one_tone.__version__ == "0.1.0"
