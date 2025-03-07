import pyotp
import qrcode

def generate_qr_code(email):
    # Generate a random secret key (store this securely for user sessions)
    secret = pyotp.random_base32()

    # Create a TOTP object
    totp = pyotp.TOTP(secret)

    # Generate provisioning URI for authenticator apps
    provisioning_uri = totp.provisioning_uri(
        name="email",
        issuer_name="My Python App"
    )

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img