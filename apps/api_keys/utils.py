from .models import APIKey
import logging
import yaml
import os
import tempfile
import configparser

logger = logging.getLogger(__name__)

def get_active_api_keys():
    """
    從資料庫抓取所有啟用的 API 金鑰，返回格式為 {service_name: key_value} 的字典。
    """
    keys = APIKey.objects.filter(is_active=True)
    return {k.service_name.lower(): k.key_value for k in keys}

def generate_subfinder_config(keys):
    """
    生成 subfinder 的 provider-config.yaml。
    """
    config = {}
    for service, value in keys.items():
        # Subfinder 期望的是一個金鑰列表
        config[service] = [value]
    
    fd, path = tempfile.mkstemp(suffix=".yaml", prefix="subfinder_")
    with os.fdopen(fd, 'w') as f:
        yaml.dump(config, f)
    return path

def generate_amass_config(keys):
    """
    生成 amass 的 config.ini。
    """
    config = configparser.ConfigParser()
    for service, value in keys.items():
        # Amass 的 INI 格式比較特別
        section = f"data_sources.{service.capitalize()}"
        config[section] = {}
        cred_section = f"{section}.credentials"
        config[cred_section] = {"apikey": value}
    
    fd, path = tempfile.mkstemp(suffix=".ini", prefix="amass_")
    with os.fdopen(fd, 'w') as f:
        config.write(f)
    return path

def generate_gau_config(keys):
    """
    生成 gau 的 .gau.toml。
    """
    lines = []
    for service, value in keys.items():
        lines.append(f"[{service}]")
        lines.append(f'apikey = "{value}"')
        lines.append("")
    
    fd, path = tempfile.mkstemp(suffix=".toml", prefix="gau_")
    with os.fdopen(fd, 'w') as f:
        f.write("\n".join(lines))
    return path

def generate_nuclei_secrets(keys):
    """
    生成 nuclei 的 secrets.yaml。
    """
    secrets = []
    for service, value in keys.items():
        secrets.append({
            "name": f"{service}_token",
            "value": value
        })
    
    fd, path = tempfile.mkstemp(suffix=".yaml", prefix="nuclei_")
    with os.fdopen(fd, 'w') as f:
        yaml.dump(secrets, f)
    return path
