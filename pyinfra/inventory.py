import os

fewaapp = [
    (
        "207.211.156.85",
        {
            "ssh_user": "deploy",
            "ssh_port": 2222,
            "ssh_key": "~/.ssh/id_ed25519",
            "ssh_strict_host_key_checking": "off",
            "_sudo": True,
            "_sudo_password": os.environ.get("SUDO_PASSWORD", ""),
        },
    )
]
