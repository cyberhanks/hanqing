-- 政治人物
CREATE TABLE politicians (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  name_en       TEXT,
  party         TEXT NOT NULL, -- DPP / KMT / TPP / IND
  role          TEXT NOT NULL, -- 立法委員 / 縣市長 / 行政院長...
  region        TEXT,          -- 選區或縣市
  term_start    DATE,
  term_end      DATE,
  avatar_url    TEXT,
  bio           TEXT,
  trust_score   INTEGER DEFAULT 50, -- 0–100，系統計算
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 承諾紀錄
CREATE TABLE promises (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID REFERENCES politicians(id),
  text            TEXT NOT NULL,
  summary         TEXT,
  topic           TEXT,
  deadline        TEXT,
  status          TEXT DEFAULT 'active',
  -- active / fulfilled / broken / stalled / unknown
  source_url      TEXT,
  source_name     TEXT,
  source_date     DATE,
  confidence      INTEGER,
  verified_by     TEXT,
  verified_at     TIMESTAMPTZ,
  evidence_url    TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 發言紀錄
CREATE TABLE statements (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID REFERENCES politicians(id),
  content         TEXT NOT NULL,
  summary         TEXT,
  topic           TEXT,
  source_url      TEXT,
  source_name     TEXT,
  statement_date  DATE,
  statement_type  TEXT, -- 質詢/記者會/社群媒體/演講
  confidence      INTEGER,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 投票紀錄
CREATE TABLE votes (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID REFERENCES politicians(id),
  bill_name       TEXT NOT NULL,
  bill_id         TEXT,
  vote_date       DATE,
  position        TEXT, -- 贊成/反對/棄權/缺席
  source_url      TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 爭議事件
CREATE TABLE events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title           TEXT NOT NULL,
  description     TEXT,
  event_date      DATE,
  event_type      TEXT, -- 爭議/醜聞/失言/法律案件
  severity        INTEGER DEFAULT 1, -- 1–5
  source_url      TEXT,
  source_name     TEXT,
  status          TEXT DEFAULT 'ongoing', -- ongoing/resolved/dismissed
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 爭議事件與政治人物的關聯（多對多）
CREATE TABLE event_politicians (
  event_id        UUID REFERENCES events(id),
  politician_id   UUID REFERENCES politicians(id),
  role            TEXT, -- 主角/相關人物
  PRIMARY KEY (event_id, politician_id)
);

-- 稽核日誌
CREATE TABLE audit_logs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  record_type     TEXT,
  record_id       UUID,
  action          TEXT,
  actor           TEXT,
  note            TEXT,
  metadata        JSONB,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 全文搜尋索引
CREATE INDEX ON statements
  USING GIN (to_tsvector('simple', content));
CREATE INDEX ON promises
  USING GIN (to_tsvector('simple', text));

-- 種子資料：5 位政治人物
INSERT INTO politicians (name, name_en, party, role, region, trust_score, bio) VALUES
('賴清德', 'Lai Ching-te', 'DPP', '總統', '全國', 52,
 '第16任中華民國總統，前行政院長、台南市長。'),
('韓國瑜', 'Han Kuo-yu', 'KMT', '立法委員', '全國不分區', 45,
 '中國國民黨籍，前高雄市長、立法院長。'),
('柯文哲', 'Ko Wen-je', 'TPP', '台灣民眾黨主席', '全國', 35,
 '台灣民眾黨創黨主席，前台北市長。'),
('卓榮泰', 'Cho Jung-tai', 'DPP', '行政院長', '全國', 50,
 '民主進步黨籍，現任行政院長。'),
('盧秀燕', 'Lu Shiow-yen', 'KMT', '台中市長', '台中市', 55,
 '中國國民黨籍，現任台中市長。');

-- 種子資料：承諾紀錄
INSERT INTO promises (politician_id, text, summary, topic, deadline, status, source_name, source_date, confidence, verified_by)
SELECT id, '推動國家氣候變遷因應法，2030 年再生能源佔比 30%', '能源轉型承諾', '能源', '2027-12-31', 'active', '就職演說', '2024-05-20', 85, 'auto'
FROM politicians WHERE name = '賴清德';

INSERT INTO promises (politician_id, text, summary, topic, deadline, status, source_name, source_date, confidence, verified_by)
SELECT id, '任期內推動憲政改革，完成修憲', '修憲承諾', '政治改革', '2028-12-31', 'active', '競選政見', '2023-11-15', 75, 'auto'
FROM politicians WHERE name = '賴清德';

INSERT INTO promises (politician_id, text, summary, topic, deadline, status, source_name, source_date, confidence, verified_by)
SELECT id, '打造台中成為亞洲宜居城市，推動大眾運輸', '城市發展承諾', '交通', '2026-12-31', 'stalled', '市長就職演說', '2022-12-25', 70, 'auto'
FROM politicians WHERE name = '盧秀燕';

INSERT INTO promises (politician_id, text, summary, topic, deadline, status, source_name, source_date, confidence, verified_by)
SELECT id, '推動《政治獻金法》修法，增加透明度', '政治透明化', '廉政', '2025-12-31', 'broken', '黨團聲明', '2024-02-10', 80, 'human'
FROM politicians WHERE name = '柯文哲';

INSERT INTO promises (politician_id, text, summary, topic, deadline, status, source_name, source_date, confidence, verified_by)
SELECT id, '降低電費負擔，推動民生電費補貼', '電費減輕方案', '民生經濟', '2025-06-30', 'fulfilled', '院長記者會', '2024-06-01', 90, 'human'
FROM politicians WHERE name = '卓榮泰';

INSERT INTO promises (politician_id, text, summary, topic, deadline, status, source_name, source_date, confidence, verified_by)
SELECT id, '嚴格執法打擊黑金，任內絕不寬貸', '廉潔執政承諾', '廉政', '2028-12-31', 'active', '競選造勢', '2024-01-05', 65, 'auto'
FROM politicians WHERE name = '韓國瑜';
