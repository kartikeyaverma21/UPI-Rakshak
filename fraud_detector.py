import re

RULES = {

    "QR Code Scam": [
        r"scan.*qr",
        r"qr.*receive",
        r"scan.*receive.*money",
        r"qr code.*payment",
        r"scan.*get.*money"
    ],

    "OTP Scam": [
        r"share.*otp",
        r"tell.*otp",
        r"give.*otp",
        r"send.*otp",
        r"share.*one.time.password",
        r"bank.*otp"
    ],

    "Fake Customer Care": [
        r"fake customer care",
        r"customer support.*otp",
        r"bank.*account.*blocked",
        r"customer care.*remote",
        r"bank employee.*pin"
    ],

    "Collect Request Scam": [
        r"collect request",
        r"approve.*payment request",
        r"request.*receive.*money",
        r"enter.*pin.*receive",
        r"payment request.*approve"
    ],

    "Screen Sharing Scam": [
        r"screen sharing",
        r"share.*screen",
        r"anydesk",
        r"teamviewer",
        r"remote access",
        r"install.*remote"
    ],

    "Fake Payment Screenshot": [
        r"fake payment screenshot",
        r"payment screenshot",
        r"screenshot.*payment",
        r"payment successful.*screenshot",
        r"fake transaction receipt"
    ]
}


def detect_fraud(message):

    text = message.lower()
    matches = []

    for scam, patterns in RULES.items():

        for pattern in patterns:

            if re.search(pattern, text):
                matches.append(scam)
                break

    if matches:

        return {
            "risk": "HIGH",
            "scams": matches,
            "reply": "Potential fraud patterns detected.",
            "explanation": (
                "Your message contains patterns associated "
                "with known UPI fraud techniques."
            ),
            "actions": [
                "Do not share your UPI PIN or OTP.",
                "Do not approve unexpected payment requests.",
                "Verify information through your official bank app.",
                "Stop communicating with suspicious callers."
            ]
        }

    suspicious_words = [
        "urgent", "prize", "reward", "blocked",
        "refund", "kyc", "verify", "lottery",
        "link", "password", "account"
    ]

    found = [word for word in suspicious_words if word in text]

    if found:

        return {
            "risk": "MEDIUM",
            "scams": [],
            "reply": "Some suspicious indicators were found.",
            "explanation": (
                "Words associated with potentially fraudulent "
                "messages were detected. More context is needed."
            ),
            "actions": [
                "Do not click unknown links.",
                "Do not share sensitive information.",
                "Contact your bank through official channels."
            ]
        }

    return {
        "risk": "UNKNOWN",
        "scams": [],
        "reply": "No known fraud pattern was identified.",
        "explanation": (
            "This does not mean the situation is safe. "
            "The detector may not recognize new or unusual scams."
        ),
        "actions": [
            "Never disclose your UPI PIN or OTP.",
            "Verify payments inside your own UPI application.",
            "Avoid unknown links and unexpected requests."
        ]
    }