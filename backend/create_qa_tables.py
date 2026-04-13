"""Create QA module tables."""
import asyncio
from app.database import engine
from sqlalchemy import text

async def create_qa_tables():
    async with engine.begin() as conn:
        # Create QA tables using raw SQL
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS qa_test_definitions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL UNIQUE,
                description TEXT,
                module VARCHAR(100) NOT NULL,
                test_type VARCHAR(50) NOT NULL,
                endpoint_url VARCHAR(500),
                http_method VARCHAR(10),
                expected_status INTEGER,
                max_response_time_ms INTEGER,
                validation_rules JSONB,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS qa_test_suites (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL UNIQUE,
                description TEXT,
                module VARCHAR(100) NOT NULL,
                test_ids JSONB,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS qa_test_results (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                test_definition_id UUID NOT NULL REFERENCES qa_test_definitions(id) ON DELETE CASCADE,
                suite_id UUID REFERENCES qa_test_suites(id) ON DELETE CASCADE,
                status VARCHAR(50) DEFAULT 'pending',
                execution_time_ms NUMERIC(10, 2),
                response_status INTEGER,
                response_data JSONB,
                error_message TEXT,
                stack_trace TEXT,
                performed_by UUID,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS qa_reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                report_name VARCHAR(200) NOT NULL,
                suite_id UUID REFERENCES qa_test_suites(id) ON DELETE CASCADE,
                total_tests INTEGER DEFAULT 0,
                passed_tests INTEGER DEFAULT 0,
                failed_tests INTEGER DEFAULT 0,
                skipped_tests INTEGER DEFAULT 0,
                error_tests INTEGER DEFAULT 0,
                execution_time_ms NUMERIC(12, 2),
                summary TEXT,
                report_data JSONB,
                file_path VARCHAR(500),
                generated_by UUID,
                generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qa_test_definitions_module ON qa_test_definitions(module)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qa_test_suites_module ON qa_test_suites(module)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qa_test_results_test_definition_id ON qa_test_results(test_definition_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qa_test_results_suite_id ON qa_test_results(suite_id)"))
        
        print("QA tables created successfully")

if __name__ == "__main__":
    asyncio.run(create_qa_tables())
