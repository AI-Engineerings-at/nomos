import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def validate_password_strength(password: str) -> list[str]:
    errors = []
    if len(password) < 12:
        errors.append("Passwort muss mindestens 12 Zeichen lang sein")
    if not any(c.isupper() for c in password):
        errors.append("Passwort muss mindestens einen Grossbuchstaben enthalten")
    if not any(c.islower() for c in password):
        errors.append("Passwort muss mindestens einen Kleinbuchstaben enthalten")
    if not any(c.isdigit() for c in password):
        errors.append("Passwort muss mindestens eine Zahl enthalten")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Passwort muss mindestens ein Sonderzeichen enthalten")
    return errors
