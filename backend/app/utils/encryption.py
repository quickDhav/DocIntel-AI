"""Fernet-based file encryption for documents at rest."""

import os
import logging
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

logger = logging.getLogger(__name__)


class FileEncryption:
    """Encrypts and decrypts files on disk using Fernet symmetric encryption.

    The encryption key is loaded from application settings.  If the key
    is the sentinel value ``auto_generated_on_first_run``, a fresh key is
    generated and written back to the ``.env`` file so it persists across
    restarts.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._key = self._resolve_key(settings)
        self._fernet = Fernet(self._key)


    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key and return it as a UTF-8 string."""
        return Fernet.generate_key().decode("utf-8")

    def _resolve_key(self, settings) -> bytes:
        """Return a valid Fernet key, auto-generating one if necessary."""
        raw = settings.ENCRYPTION_KEY
        if raw == "auto_generated_on_first_run" or not raw:
            new_key = self.generate_key()
            self._persist_key_to_env(settings, new_key)
            settings.ENCRYPTION_KEY = new_key
            logger.info("Auto-generated new encryption key and saved to .env")
            return new_key.encode("utf-8")
        return raw.encode("utf-8")

    @staticmethod
    def _persist_key_to_env(settings, key: str) -> None:
        """Write the generated key into the .env file."""
        env_path = os.path.join(settings.BASE_DIR, ".env")
        lines: list[str] = []
        key_found = False

        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("ENCRYPTION_KEY="):
                        lines.append(f"ENCRYPTION_KEY={key}\n")
                        key_found = True
                    else:
                        lines.append(line)

        if not key_found:
            lines.append(f"ENCRYPTION_KEY={key}\n")

        with open(env_path, "w", encoding="utf-8") as fh:
            fh.writelines(lines)


    def encrypt_file(self, input_path: str) -> str:
        """Encrypt a file on disk and return the path to the encrypted file.

        The encrypted file is written alongside the original with an
        ``.enc`` extension.  The original file is removed after
        successful encryption.

        Args:
            input_path: Absolute path to the plaintext file.

        Returns:
            Absolute path to the encrypted file.
        """
        input_path_obj = Path(input_path)
        encrypted_path = input_path_obj.with_suffix(input_path_obj.suffix + ".enc")

        with open(input_path, "rb") as f_in:
            plaintext = f_in.read()

        ciphertext = self._fernet.encrypt(plaintext)

        with open(encrypted_path, "wb") as f_out:
            f_out.write(ciphertext)

        os.remove(input_path)
        logger.debug("Encrypted %s -> %s", input_path, encrypted_path)
        return str(encrypted_path)

    def decrypt_file(self, encrypted_path: str) -> bytes:
        """Decrypt a file and return its contents in memory.

        The decrypted content is never written to disk.

        Args:
            encrypted_path: Absolute path to the ``.enc`` file.

        Returns:
            Decrypted file bytes.

        Raises:
            InvalidToken: If decryption fails (wrong key or corrupt data).
        """
        with open(encrypted_path, "rb") as fh:
            ciphertext = fh.read()

        try:
            plaintext = self._fernet.decrypt(ciphertext)
        except InvalidToken:
            logger.error("Failed to decrypt %s — invalid token", encrypted_path)
            raise

        return plaintext
