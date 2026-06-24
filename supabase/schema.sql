-- つるまい移動支援システム — DBスキーマ
-- Supabaseプロジェクト: ftemqjfkibpprtvitgph

-- === 1. 利用者マスタ ===
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  phone TEXT,
  address TEXT,
  zip_code TEXT,
  is_regular BOOLEAN DEFAULT FALSE,           -- 常連（30分枠特権）
  home_location_id TEXT REFERENCES locations(location_id),  -- 自宅の場所
  reservation_count INTEGER DEFAULT 0,
  name_variants JSONB DEFAULT '[]',           -- 表記ゆれ（AI補完用）
  notes TEXT,                                 -- 生の声・特記事項
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- === 2. 場所マスタ ===
CREATE TABLE IF NOT EXISTS locations (
  location_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('home','medical','dental','commercial','station','housing','public','shop','finance','other')),
  address TEXT,
  google_maps_url TEXT,
  latitude REAL,
  longitude REAL,
  pin_confirmed BOOLEAN DEFAULT FALSE,        -- Googleマップピン確定済
  pin_rank TEXT DEFAULT 'B' CHECK (pin_rank IN ('S','A','B')),  -- S=確定/A=住所/B=要確認
  reference_count INTEGER DEFAULT 0,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- === 3. 運行ルール ===
CREATE TABLE IF NOT EXISTS operation_rules (
  rule_id TEXT PRIMARY KEY,
  rule_name TEXT NOT NULL,
  rule_value JSONB NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- === 4. 予約台帳（コア）===
CREATE TABLE IF NOT EXISTS reservations (
  reservation_id BIGSERIAL PRIMARY KEY,
  user_id TEXT REFERENCES users(user_id),
  user_name_snapshot TEXT NOT NULL,           -- 利用者名スナップショット
  reservation_date DATE NOT NULL,
  start_time TIME NOT NULL,
  duration_minutes INTEGER DEFAULT 20 CHECK (duration_minutes IN (20,30)),
  pickup_location_id TEXT REFERENCES locations(location_id),
  pickup_location_snapshot TEXT,
  dropoff_location_id TEXT REFERENCES locations(location_id),
  dropoff_location_snapshot TEXT,
  is_round_trip BOOLEAN DEFAULT FALSE,
  status TEXT DEFAULT 'pending' CHECK (status IN ('draft','pending_approval','approved','assigned','completed','cancelled','no_show')),
  channel TEXT DEFAULT 'phone-ai' CHECK (channel IN ('phone-ai','phone-manual','manual','web')),
  notes TEXT,
  transcript TEXT,                            -- 通話文字起こし（参考）
  received_by TEXT,                           -- 受付ボランティア
  approved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- === 5. 通話ログ ===
CREATE TABLE IF NOT EXISTS call_logs (
  call_id BIGSERIAL PRIMARY KEY,
  caller_phone TEXT,
  user_id TEXT REFERENCES users(user_id),
  started_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  transcript TEXT,
  ai_summary TEXT,
  final_status TEXT,
  transferred_to_human BOOLEAN DEFAULT FALSE,
  audio_url TEXT,
  consent_obtained BOOLEAN DEFAULT FALSE
);

-- === インデックス ===
CREATE INDEX IF NOT EXISTS idx_reservations_date ON reservations(reservation_date, start_time);
CREATE INDEX IF NOT EXISTS idx_reservations_user ON reservations(user_id);
CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);
CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(type);
CREATE INDEX IF NOT EXISTS idx_users_regular ON users(is_regular) WHERE is_regular = TRUE;

-- === RLS（Row Level Security）===
-- 本番運用前は一時的に無効化（開発フェーズ）
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE operation_rules ENABLE ROW LEVEL SECURITY;

-- 開発用：認証済みユーザーは全件アクセス可（本番前に制限）
CREATE POLICY "dev_all_authenticated" ON users FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "dev_all_authenticated" ON locations FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "dev_all_authenticated" ON reservations FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "dev_all_authenticated" ON call_logs FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "dev_all_authenticated" ON operation_rules FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- === 初期データ：運行ルール ===
INSERT INTO operation_rules (rule_id, rule_name, rule_value, description) VALUES
('R1', 'operation_days', '["月","水","金"]'::jsonb, '運行曜日'),
('R2', 'operation_hours', '[{"start":"09:00","end":"12:00"},{"start":"13:00","end":"16:00"}]'::jsonb, '運行時間帯（昼休み12-13時除く）'),
('R3', 'default_duration_minutes', '20'::jsonb, '標準所要時間'),
('R4', 'max_per_hour', '3'::jsonb, '1時間あたり最大件数（20分枠時）'),
('R5', 'long_duration_minutes', '30'::jsonb, '常連特権の所要時間'),
('R6', 'long_duration_eligible', 'is_regular = true'::jsonb, '30分枠は常連のみ'),
('R7', 'reservation_acceptance', 'anytime'::jsonb, '予約受付はいつでも可（運行日以外の予約も前倒しで受付）'),
('R8', 'vehicle_assignment', 'out_of_scope'::jsonb, '運転手割当は当面システム外（1台1運転手）')
ON CONFLICT (rule_id) DO NOTHING;

COMMENT ON TABLE reservations IS 'つるまい移動支援 予約台帳。電話AI/手動/Webどの経路でも同じスキーマに書き込む';
COMMENT ON COLUMN users.is_regular IS '常連フラグ。30分枠（所要時間30分）は常連のみ許可';
COMMENT ON COLUMN locations.pin_rank IS 'S=Googleマップピン確定済/A=住所あり/B=要確認（現場で育てる）';
