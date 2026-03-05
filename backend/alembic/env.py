from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import table models so SQLModel.metadata is populated for autogenerate.
import models.email_verification_token  # noqa: F401,E402
import models.password_reset_token  # noqa: F401,E402
import models.refresh_token  # noqa: F401,E402
import models.system_settings  # noqa: F401,E402
import models.ui_label  # noqa: F401,E402
import models.ui_label_suggestions  # noqa: F401,E402
import models.ui_locale  # noqa: F401,E402
import models.user  # noqa: F401,E402
import models.user_settings  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_type = os.getenv("DB_TYPE", "sqlite")
if db_type != "sqlite":
    raise RuntimeError(f"Unsupported DB_TYPE for Alembic: {db_type}. Only sqlite is supported.")
sqlite_db_path = os.getenv("SQLITE_DB_PATH", "app.db")
config.set_main_option("sqlalchemy.url", f"sqlite:///{sqlite_db_path}")

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
