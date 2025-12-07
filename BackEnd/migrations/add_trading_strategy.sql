-- Migration SQL Script: Add TradingStrategy column to Accounts table
-- Run this in your PostgreSQL database

-- Check if column exists (optional, for safety)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='Accounts' 
        AND column_name='TradingStrategy'
    ) THEN
        -- Add the column
        ALTER TABLE "Accounts" 
        ADD COLUMN "TradingStrategy" VARCHAR(20) DEFAULT 'None';
        
        RAISE NOTICE 'TradingStrategy column added successfully!';
    ELSE
        RAISE NOTICE 'TradingStrategy column already exists!';
    END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name='Accounts' 
AND column_name='TradingStrategy';
