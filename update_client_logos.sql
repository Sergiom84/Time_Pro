-- SQL Script to update client logo URLs
-- This script updates the logo_url field for each client with their Supabase Storage URLs
--
-- BEFORE RUNNING:
-- 1. Ensure all logo files are in Storage > Buckets > Logos (public)
-- 2. Obtain the full public URLs for each client's logo
-- 3. Replace the placeholder URLs below with the actual URLs from Supabase
--
-- URL Format:
-- https://gqesfclbingbihakiojm.supabase.co/storage/v1/object/public/Logos/{FILENAME}

-- Update Time Pro (client_id=1) logo
UPDATE client
SET logo_url = 'https://gqesfclbingbihakiojm.supabase.co/storage/v1/object/public/Logos/Time_Pro.JPG'
WHERE id = 1 AND name = 'Time Pro';

-- Update PruebaCo (client_id=2) logo
UPDATE client
SET logo_url = 'https://gqesfclbingbihakiojm.supabase.co/storage/v1/object/public/Logos/PruebaCo.JPG'
WHERE id = 2 AND name = 'PruebaCo';

-- Aluminios Lara (client_id=4) logo is already updated
-- UPDATE client
-- SET logo_url = 'https://gqesfclbingbihakiojm.supabase.co/storage/v1/object/public/Logos/Aluminios_Lara.JPG'
-- WHERE id = 4 AND name = 'Aluminios Lara';

-- Verify all logos are set
SELECT id, name, logo_url FROM client WHERE id IN (1, 2, 4) ORDER BY id;
