export type Evidence = { ticket_id?: string; quote: string; start?: number; end?: number };

export type Analysis = {
  summary: string;
  problem_type: string;
  product_area: string;
  sentiment: string;
  suggested_owner: string;
  severity: string;
  needs_escalation: boolean;
  review_status: string;
  root_cause_hypothesis?: string | null;
  evidence_spans: Evidence[];
  analysis_source: string;
};

export type Ticket = {
  id: string;
  ticket_id: string;
  user_type: string;
  channel: string;
  message: string;
  created_at: string;
  analysis?: Analysis | null;
};

export type Cluster = {
  id: string;
  title: string;
  summary: string;
  member_count: number;
  severity: string;
  trend: string;
  suggested_owner: string;
  representative_ticket_ids: string[];
  evidence: Evidence[];
};

export type SOPCandidate = {
  id: string;
  cluster_id: string;
  title: string;
  applicable_when: string;
  steps: string[];
  suggested_reply: string;
  escalation_condition: string;
  prohibited_actions: string[];
  evidence_ticket_ids: string[];
  session_status: string;
};

