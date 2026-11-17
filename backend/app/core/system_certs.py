"""Optional: verify TLS against the operating system's certificate store.

Some networks and company laptops re-sign HTTPS traffic with their own root
certificate. Python's bundled certificate list does not know it, so downloads
fail with "self-signed certificate in certificate chain". With
ANSIT_SYSTEM_CERTS=1 the scripts trust whatever the operating system trusts
(Windows certificate store, macOS keychain, the Linux CA directory) instead.

This never disables verification.
"""

import os


def use_system_certs_if_requested() -> bool:
    if os.environ.get("ANSIT_SYSTEM_CERTS", "").lower() not in ("1", "true", "yes"):
        return False
    import truststore

    truststore.inject_into_ssl()
    # Hugging Face's optional Rust downloader has its own TLS stack; use the
    # plain HTTPS path, which goes through Python's ssl module.
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    return True
