-- Script para cambiar la estructura de categorías de ENUM a FK
-- Se ejecuta directamente en Supabase

-- Step 1: Add category_id column if it doesn't exist
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS category_id INTEGER;

-- Step 2: Add FK constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                   WHERE constraint_name = 'fk_user_category_id' AND table_name = 'user') THEN
        ALTER TABLE "user" ADD CONSTRAINT fk_user_category_id
            FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Step 3: Verify changes
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'user' AND column_name IN ('categoria', 'category_id');

-- Step 4: Show FK constraints on user table
SELECT constraint_name, column_name FROM information_schema.constraint_column_usage
WHERE table_name = 'user' AND constraint_name LIKE '%category%';
