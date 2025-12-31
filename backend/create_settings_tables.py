import asyncio
from sqlalchemy import text
from db.database import async_session

async def create_tables():
    async with async_session() as db:
        # Create user_settings table
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                ai_role VARCHAR(50) DEFAULT 'partner_strategic',
                thinking_depth VARCHAR(30) DEFAULT 'structured',
                response_style VARCHAR(20) DEFAULT 'detailed',
                confrontation_level VARCHAR(20) DEFAULT 'argumented',
                initiative_level VARCHAR(30) DEFAULT 'suggest',
                intervention_frequency VARCHAR(30) DEFAULT 'realtime',
                allowed_actions JSONB DEFAULT '["create_decisions", "link_memories"]',
                save_policy VARCHAR(30) DEFAULT 'save_confirmed',
                auto_archive_days INTEGER DEFAULT 365,
                memory_trust_level VARCHAR(20) DEFAULT 'cautious',
                saved_types JSONB DEFAULT '["facts", "decisions", "hypotheses"]',
                analytics_types JSONB DEFAULT '["logical_contradictions", "recurring_topics"]',
                analytics_aggressiveness VARCHAR(30) DEFAULT 'recommend',
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """))
        
        # Create rules table
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS rules (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                scope VARCHAR(20) NOT NULL DEFAULT 'global',
                trigger VARCHAR(30) NOT NULL DEFAULT 'always',
                instruction TEXT NOT NULL,
                priority VARCHAR(20) DEFAULT 'normal',
                is_active BOOLEAN DEFAULT true,
                context_topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
                context_mode VARCHAR(50),
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """))
        
        # Create indexes
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_rules_user ON rules(user_id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_rules_scope ON rules(scope)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_rules_active ON rules(is_active)"))
        
        await db.commit()
        print("Tables created successfully!")

asyncio.run(create_tables())
