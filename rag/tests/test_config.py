"""确保不同平台的密钥不会混用，验证百炼批量参数。"""
import os
import unittest
from unittest.mock import patch
from config_data import get_settings


class ConfigurationTests(unittest.TestCase):
    def test_different_provider_requires_embedding_key(self):
        with patch.dict(os.environ, {
            'AI_API_KEY': 'other-provider-test-key', 'AI_BASE_URL': 'https://other.invalid/v1',
            'EMBEDDING_BASE_URL': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        }, clear=True):
            settings = get_settings()
            self.assertEqual(settings.embedding_key, '')
            with self.assertRaisesRegex(ValueError, 'EMBEDDING_API_KEY'):
                settings.validate()

    def test_bailian_chat_can_reuse_key(self):
        with patch.dict(os.environ, {
            'AI_API_KEY': 'bailian-test-key',
            'AI_BASE_URL': 'https://workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1',
            'EMBEDDING_BASE_URL': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        }, clear=True):
            settings = get_settings()
            self.assertEqual(settings.embedding_key, 'bailian-test-key')
            settings.validate()

    def test_rejects_batch_above_ten(self):
        with patch.dict(os.environ, {'AI_API_KEY': 'test', 'EMBEDDING_BATCH_SIZE': '11'}, clear=True):
            with self.assertRaisesRegex(ValueError, '1到10'):
                get_settings().validate()
