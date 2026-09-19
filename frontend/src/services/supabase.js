import { createClient } from  '@supabase/supabase-js'

const SUPABASE_URL = 'https://bwugsjjpbcoxfdppnoha.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ3dWdzampwYmNveGZkcHBub2hhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4MTA5MDAsImV4cCI6MjEwNTM4NjkwMH0.kx6tuUwVtGoSnSLbZ5B3EKBY66mwOase8uC6ZrQp6RQ'

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)