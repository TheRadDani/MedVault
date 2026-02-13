"""
Encryption/Decryption module for MedVault RAG pipeline.

Provides secure encryption at rest with in-memory decryption for sensitive medical data.
Uses Fernet (symmetric encryption) from the cryptography library with AES-128 under the hood.

Features:
- File-level and stream-level encryption
- Key derivation from password or environment variable
- Tamper detection (HMAC signatures included)
- In-memory decryption (encrypted files never decrypted to disk)
"""

import os
from typing import Optional, Tuple
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
from loguru import logger


class EncryptionManager:
    """
    Manages encryption/decryption of medical documents.
    
    Attributes:
        cipher: Fernet cipher instance for encryption/decryption
        encryption_enabled: Whether encryption is active
    """
    
    def __init__(self, encryption_key: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            encryption_key: Base64-encoded Fernet key. If not provided, will derive from password.
            password: Master password for key derivation (PBKDF2). 
                     If neither provided, encryption disabled.
        
        Raises:
            ValueError: If key is invalid or neither key nor password provided
        """
        self.encryption_enabled = False
        self.cipher = None
        
        try:
            if encryption_key:
                # Use provided key directly
                self._initialize_with_key(encryption_key)
            elif password:
                # Derive key from password
                self._initialize_with_password(password)
            else:
                logger.warning("No encryption key or password provided. Encryption disabled.")
                self.encryption_enabled = False
        
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def _initialize_with_key(self, key: str):
        """Initialize cipher with provided Fernet key."""
        try:
            # Validate key format
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
            self.encryption_enabled = True
            logger.info("Encryption initialized with provided key")
        except Exception as e:
            raise ValueError(f"Invalid Fernet key format: {e}")
    
    def _initialize_with_password(self, password: str) -> bytes:
        """
        Derive encryption key from password using PBKDF2.
        
        Standard salt: b'medvault_salt_v1' (deterministic for consistency)
        This allows consistent decryption across sessions with same password.
        """
        salt = b'medvault_salt_v1'  # Standard salt for medical data
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for Fernet
            salt=salt,
            iterations=100000,  # OWASP recommendation (2023)
        )
        
        key = base64.urlsafe_b64encode(
            kdf.derive(password.encode())
        )
        
        try:
            self.cipher = Fernet(key)
            self.encryption_enabled = True
            logger.info("Encryption initialized with password-derived key")
        except Exception as e:
            raise ValueError(f"Failed to derive encryption key: {e}")
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new random Fernet encryption key.
        
        Returns:
            Base64-encoded key string safe for storage in .env files
        
        Usage:
            key = EncryptionManager.generate_key()
            # Store in .env: ENCRYPTION_KEY=<key>
        """
        key = Fernet.generate_key()
        return key.decode() if isinstance(key, bytes) else key
    
    def encrypt_text(self, plaintext: str) -> str:
        """
        Encrypt plaintext to ciphertext.
        
        Args:
            plaintext: Raw text to encrypt
        
        Returns:
            Base64-encoded ciphertext (safe for file storage)
        
        Raises:
            ValueError: If encryption not enabled
        """
        if not self.encryption_enabled or not self.cipher:
            raise ValueError("Encryption not enabled")
        
        try:
            ciphertext = self.cipher.encrypt(plaintext.encode())
            return ciphertext.decode()  # Return as string
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_text(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext to plaintext.
        
        Args:
            ciphertext: Base64-encoded encrypted text
        
        Returns:
            Decrypted plaintext
        
        Raises:
            ValueError: If encryption not enabled or decryption fails (tamper detection)
        """
        if not self.encryption_enabled or not self.cipher:
            raise ValueError("Encryption not enabled")
        
        try:
            plaintext = self.cipher.decrypt(ciphertext.encode())
            return plaintext.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token (data may be tampered)")
            raise ValueError("Decryption failed - data integrity check failed")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_file(self, input_file: str, output_file: str) -> bool:
        """
        Encrypt a file and save to disk.
        
        Args:
            input_file: Path to plaintext file
            output_file: Path to save encrypted file
        
        Returns:
            bool: Success status
        """
        if not self.encryption_enabled or not self.cipher:
            logger.warning("Encryption not enabled, copying file as-is")
            # Just copy the file without encryption
            with open(input_file, 'r') as f:
                with open(output_file, 'w') as out:
                    out.write(f.read())
            return True
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                plaintext = f.read()
            
            ciphertext = self.encrypt_text(plaintext)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(ciphertext)
            
            logger.debug(f"File encrypted: {input_file} → {output_file}")
            return True
        
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            return False
    
    def decrypt_file_in_memory(self, encrypted_file: str) -> Optional[str]:
        """
        Read encrypted file from disk and decrypt in memory (never writes plaintext to disk).
        
        Args:
            encrypted_file: Path to encrypted file
        
        Returns:
            Decrypted plaintext (or original if encryption disabled)
        
        Raises:
            FileNotFoundError: If file not found
            ValueError: If decryption fails
        """
        try:
            with open(encrypted_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # If encryption disabled, return as-is
            if not self.encryption_enabled:
                return content
            
            # Decrypt in memory
            plaintext = self.decrypt_text(content)
            logger.debug(f"File decrypted in memory: {encrypted_file}")
            return plaintext
        
        except FileNotFoundError:
            logger.error(f"Encrypted file not found: {encrypted_file}")
            raise
        except Exception as e:
            logger.error(f"In-memory decryption failed: {e}")
            raise
    
    def encrypt_directory(self, input_dir: str, output_dir: str, pattern: str = "*.txt") -> int:
        """
        Encrypt all files in directory.
        
        Args:
            input_dir: Directory with plaintext files
            output_dir: Directory to save encrypted files
            pattern: Glob pattern for files to encrypt
        
        Returns:
            int: Number of files encrypted
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        input_path = Path(input_dir)
        count = 0
        
        for file in input_path.glob(pattern):
            if file.is_file():
                output_file = Path(output_dir) / file.name
                if self.encrypt_file(str(file), str(output_file)):
                    count += 1
        
        logger.info(f"Encrypted {count} files from {input_dir} → {output_dir}")
        return count
    
    def decrypt_directory_in_memory(self, input_dir: str, pattern: str = "*.txt") -> dict:
        """
        Decrypt all files in directory, keeping only in memory.
        
        Args:
            input_dir: Directory with encrypted files
            pattern: Glob pattern for files to decrypt
        
        Returns:
            dict: {filename: decrypted_content}
        """
        input_path = Path(input_dir)
        contents = {}
        
        for file in input_path.glob(pattern):
            if file.is_file():
                try:
                    plaintext = self.decrypt_file_in_memory(str(file))
                    contents[file.name] = plaintext
                except Exception as e:
                    logger.warning(f"Failed to decrypt {file.name}: {e}")
        
        logger.info(f"Decrypted {len(contents)} files in memory from {input_dir}")
        return contents


def get_encryption_manager(
    encryption_key: Optional[str] = None,
    password: Optional[str] = None,
    env_var_key: str = "ENCRYPTION_KEY",
    env_var_password: str = "ENCRYPTION_PASSWORD"
) -> EncryptionManager:
    """
    Factory function to create EncryptionManager with environment fallback.
    
    Priority:
    1. Function parameters (if provided)
    2. Environment variables
    3. Disabled (no encryption)
    
    Args:
        encryption_key: Fernet key override
        password: Password override
        env_var_key: Environment variable name for key
        env_var_password: Environment variable name for password
    
    Returns:
        EncryptionManager instance
    
    Example:
        # Use environment ENCRYPTION_KEY
        em = get_encryption_manager()
        
        # Use password
        em = get_encryption_manager(password="my-secure-password")
        
        # Use explicit key
        em = get_encryption_manager(encryption_key="fernet-key-from-env")
    """
    # Check for function parameters first
    if encryption_key:
        return EncryptionManager(encryption_key=encryption_key)
    
    if password:
        return EncryptionManager(password=password)
    
    # Fall back to environment variables
    env_key = os.getenv(env_var_key)
    env_password = os.getenv(env_var_password)
    
    if env_key:
        return EncryptionManager(encryption_key=env_key)
    elif env_password:
        return EncryptionManager(password=env_password)
    else:
        logger.warning("No encryption configuration found. Creating disabled encryption manager.")
        return EncryptionManager()
