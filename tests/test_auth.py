from app.auth import create_token, hash_password, verify_password


def test_password_hash_is_salted_and_verifiable():
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong password", first)


def test_token_contains_user_identity():
    token = create_token(42, "tester")
    assert isinstance(token, str) and token.count(".") == 2
