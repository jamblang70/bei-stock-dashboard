"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("email_verified", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # --- refresh_tokens ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # --- login_attempts ---
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ip_address", postgresql.INET(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("success", sa.Boolean(), nullable=False),
    )

    # --- stocks ---
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100)),
        sa.Column("sub_sector", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("listing_date", sa.Date()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # --- stock_prices ---
    op.create_table(
        "stock_prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("price", sa.Numeric(15, 2), nullable=False),
        sa.Column("open", sa.Numeric(15, 2)),
        sa.Column("high", sa.Numeric(15, 2)),
        sa.Column("low", sa.Numeric(15, 2)),
        sa.Column("close", sa.Numeric(15, 2)),
        sa.Column("volume", sa.BigInteger()),
        sa.Column("change_nominal", sa.Numeric(15, 2)),
        sa.Column("change_pct", sa.Numeric(8, 4)),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # --- price_history ---
    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(15, 2)),
        sa.Column("high", sa.Numeric(15, 2)),
        sa.Column("low", sa.Numeric(15, 2)),
        sa.Column("close", sa.Numeric(15, 2), nullable=False),
        sa.Column("volume", sa.BigInteger()),
        sa.Column("adjusted_close", sa.Numeric(15, 2)),
        sa.UniqueConstraint("stock_id", "date", name="uq_price_history_stock_date"),
    )

    # --- fundamental_data ---
    op.create_table(
        "fundamental_data",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("period_type", sa.String(10), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("per", sa.Numeric(10, 4)),
        sa.Column("pbv", sa.Numeric(10, 4)),
        sa.Column("ev_ebitda", sa.Numeric(10, 4)),
        sa.Column("roe", sa.Numeric(10, 4)),
        sa.Column("roa", sa.Numeric(10, 4)),
        sa.Column("net_profit_margin", sa.Numeric(10, 4)),
        sa.Column("current_ratio", sa.Numeric(10, 4)),
        sa.Column("debt_to_equity", sa.Numeric(10, 4)),
        sa.Column("dividend_yield", sa.Numeric(10, 4)),
        sa.Column("dividend_per_share", sa.Numeric(15, 4)),
        sa.Column("beta", sa.Numeric(10, 4)),
        sa.Column("volatility_30d", sa.Numeric(10, 4)),
        sa.Column("revenue", sa.BigInteger()),
        sa.Column("net_income", sa.BigInteger()),
        sa.Column("total_assets", sa.BigInteger()),
        sa.Column("total_equity", sa.BigInteger()),
        sa.Column("total_debt", sa.BigInteger()),
        sa.Column("ebitda", sa.BigInteger()),
        sa.Column("eps", sa.Numeric(15, 4)),
        sa.Column("book_value_per_share", sa.Numeric(15, 4)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("stock_id", "period_type", "period_year", name="uq_fundamental_data_stock_period"),
    )

    # --- stock_scores ---
    op.create_table(
        "stock_scores",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("valuation_score", sa.Numeric(5, 2)),
        sa.Column("quality_score", sa.Numeric(5, 2)),
        sa.Column("momentum_score", sa.Numeric(5, 2)),
        sa.Column("is_partial", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("recommendation", sa.String(20)),
        sa.Column("score_factors", postgresql.JSONB()),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # --- watchlists ---
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "stock_id", name="uq_watchlists_user_stock"),
    )

    # --- ai_analysis ---
    op.create_table(
        "ai_analysis",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.String(20), nullable=False),
        sa.Column("valuation_analysis", sa.Text()),
        sa.Column("quality_analysis", sa.Text()),
        sa.Column("momentum_analysis", sa.Text()),
        sa.Column("supporting_factors", postgresql.JSONB()),
        sa.Column("data_sufficiency", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("missing_data_info", sa.Text()),
        sa.Column("model_used", sa.String(100)),
        sa.Column("prompt_version", sa.String(20)),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # --- sector_metrics ---
    op.create_table(
        "sector_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("median_per", sa.Numeric(10, 4)),
        sa.Column("median_pbv", sa.Numeric(10, 4)),
        sa.Column("median_roe", sa.Numeric(10, 4)),
        sa.Column("median_div_yield", sa.Numeric(10, 4)),
        sa.Column("stock_count", sa.Integer()),
        sa.Column("calculated_at", sa.Date(), nullable=False),
        sa.UniqueConstraint("sector", "calculated_at", name="uq_sector_metrics_sector_date"),
    )

    # --- corporate_actions ---
    op.create_table(
        "corporate_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("action_date", sa.Date(), nullable=False),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("announced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # --- data_source_health ---
    op.create_table(
        "data_source_health",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_name", sa.String(100), nullable=False),
        sa.Column("is_healthy", sa.Boolean(), nullable=False),
        sa.Column("last_success", sa.DateTime(timezone=True)),
        sa.Column("last_failure", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ---- Indexes ----
    op.create_index("idx_stocks_code", "stocks", ["code"])
    op.create_index("idx_stocks_sector", "stocks", ["sector"])
    op.create_index("idx_stock_scores_score", "stock_scores", [sa.text("score DESC")])
    op.create_index("idx_stock_scores_stock_id", "stock_scores", ["stock_id"])
    op.create_index("idx_price_history_stock_date", "price_history", [sa.text("stock_id, date DESC")])
    op.create_index("idx_fundamental_data_stock_period", "fundamental_data", [sa.text("stock_id, period_year DESC")])
    op.create_index("idx_watchlists_user", "watchlists", ["user_id"])
    op.create_index("idx_ai_analysis_stock", "ai_analysis", [sa.text("stock_id, generated_at DESC")])
    op.create_index("idx_login_attempts_ip", "login_attempts", [sa.text("ip_address, attempted_at DESC")])


def downgrade() -> None:
    op.drop_index("idx_login_attempts_ip", table_name="login_attempts")
    op.drop_index("idx_ai_analysis_stock", table_name="ai_analysis")
    op.drop_index("idx_watchlists_user", table_name="watchlists")
    op.drop_index("idx_fundamental_data_stock_period", table_name="fundamental_data")
    op.drop_index("idx_price_history_stock_date", table_name="price_history")
    op.drop_index("idx_stock_scores_stock_id", table_name="stock_scores")
    op.drop_index("idx_stock_scores_score", table_name="stock_scores")
    op.drop_index("idx_stocks_sector", table_name="stocks")
    op.drop_index("idx_stocks_code", table_name="stocks")

    op.drop_table("data_source_health")
    op.drop_table("corporate_actions")
    op.drop_table("sector_metrics")
    op.drop_table("ai_analysis")
    op.drop_table("watchlists")
    op.drop_table("stock_scores")
    op.drop_table("fundamental_data")
    op.drop_table("price_history")
    op.drop_table("stock_prices")
    op.drop_table("stocks")
    op.drop_table("login_attempts")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
