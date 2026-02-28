export type ChatResponse = {
  status: string;
  response: string;
  intent?: string | null;
  user_id: string;
};

export type ApplicantStatus =
  | "NEW"
  | "SCREENED"
  | "INTERVIEW"
  | "REJECTED"
  | "HIRED";

export type Applicant = {
  id: number;
  name: string;
  email: string;
  phone: string;
  position: string;
  cv_url?: string | null;
  cv_path?: string | null;
  status: ApplicantStatus;
  created_at: string;
};

export type ScreeningBreakdown = {
  required_skills: {
    found: string[];
    percentage: number;
    points: number;
  };
  preferred_skills: {
    found: string[];
    percentage: number;
    points: number;
  };
  experience: {
    years_found: number;
    years_required: number;
    points: number;
  };
  education: {
    relevant: boolean;
    points: number;
  };
  certifications: {
    found: string[];
    points: number;
  };
  [key: string]: any;
};

export type ScreeningRecommendation =
  | "STRONG_PASS"
  | "PASS"
  | "MAYBE"
  | "REJECT";

export type ScreeningResult = {
  id: number;
  applicant_id: number;
  position: string;
  total_score: number;
  max_score: number;
  percentage: number;
  recommendation: ScreeningRecommendation;
  status: string;
  action: string;
  breakdown: ScreeningBreakdown;
  min_score: number;
  created_at: string;
};

export type JobRequirement = {
  id: number;
  position: string;
  required_skills: any;
  preferred_skills: any;
  min_experience_years: number;
  education_keywords: any;
  certifications: any;
  min_score: number;
  created_at: string;
};

export type ChatRequestPayload = {
  user_id: string;
  message: string;
  api_key?: string | null;
};

export type CreateApplicantPayload = {
  name: string;
  email: string;
  phone: string;
  position: string;
  cv_path?: string | null;
  cv_url?: string | null;
};

export type UpdateApplicantPayload = Partial<
  Omit<Applicant, "id" | "created_at">
>;

export type RunScreeningResponse = {
  count: number;
  results: ScreeningResult[];
};

