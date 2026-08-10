"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Loader2, Pencil, RotateCw, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import type {
  AiEntities,
  AiRecommendation,
  AiRetryStage,
  AiStatus,
  ClinicalSummary,
  ConfidenceLevel,
  SoapNote,
} from "@/types/ai";

interface AiAssistantPanelProps {
  aiStatus: AiStatus;
  soap: SoapNote | null;
  summary: ClinicalSummary | null;
  entities: AiEntities | null;
  recommendations: AiRecommendation[];
  readOnly: boolean;
  onRetry: (stage: AiRetryStage) => void;
  retryPending: boolean;
  onSaveSoap: (payload: Record<string, string>) => void;
  savingSoap: boolean;
  onSaveSummary: (payload: Record<string, string>) => void;
  savingSummary: boolean;
}

const CONFIDENCE_VARIANT: Record<ConfidenceLevel, "success" | "warning" | "danger"> = {
  high: "success",
  medium: "warning",
  low: "danger",
};

function ConfidenceBadge({ level }: { level: ConfidenceLevel | null | undefined }) {
  if (!level) return null;
  return (
    <Badge variant={CONFIDENCE_VARIANT[level]} className="capitalize">
      {level} confidence
    </Badge>
  );
}

function ProcessingNotice({ aiStatus }: { aiStatus: AiStatus }) {
  if (aiStatus.stage === "queued" || aiStatus.stage.startsWith("processing")) {
    return (
      <div className="bg-muted flex items-center gap-2 rounded-md border border-border px-3 py-2 text-caption text-text-secondary">
        <Loader2 className="h-3.5 w-3.5 animate-spin" /> AI processing is running…
      </div>
    );
  }
  if (aiStatus.degraded && aiStatus.stage === "failed") {
    return (
      <div className="flex items-start gap-2 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-caption text-danger">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        <span>{aiStatus.reason ?? "AI processing failed for one or more stages."}</span>
      </div>
    );
  }
  return null;
}

// Right Panel — AI Assistant (PRD Ch9.7). Renders the real AI-generated
// SOAP note, clinical summary, extracted findings, and recommendations,
// editable by the doctor and clearly distinguishing AI-generated from
// doctor-edited content (Ch10.13-10.14) — restrained, clinical styling,
// no decorative AI animation.
export function AiAssistantPanel({
  aiStatus,
  soap,
  summary,
  entities,
  recommendations,
  readOnly,
  onRetry,
  retryPending,
  onSaveSoap,
  savingSoap,
  onSaveSummary,
  savingSummary,
}: AiAssistantPanelProps) {
  return (
    <aside className="flex w-[300px] shrink-0 flex-col gap-4 overflow-y-auto border-l border-border bg-surface p-6 lg:w-[380px]">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <h2 className="text-h5 text-text-primary">AI Assistant</h2>
      </div>

      <ProcessingNotice aiStatus={aiStatus} />

      {aiStatus.stage === "no_ai_content" && !soap && !summary && (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border p-8 text-center">
          <Sparkles className="h-6 w-6 text-text-secondary" />
          <p className="text-body text-text-secondary">
            {aiStatus.reason ?? "No AI content is available."}
          </p>
        </div>
      )}

      {(soap ||
        summary ||
        entities ||
        recommendations.length > 0 ||
        aiStatus.stage !== "no_ai_content") && (
        <Tabs defaultValue="soap">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="soap">SOAP</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="findings">Findings</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
          </TabsList>

          <TabsContent value="soap">
            <SoapTab
              soap={soap}
              readOnly={readOnly}
              onSave={onSaveSoap}
              saving={savingSoap}
              onRetry={() => onRetry("soap")}
              retryPending={retryPending}
            />
          </TabsContent>

          <TabsContent value="summary">
            <SummaryTab
              summary={summary}
              readOnly={readOnly}
              onSave={onSaveSummary}
              saving={savingSummary}
              onRetry={() => onRetry("summary")}
              retryPending={retryPending}
            />
          </TabsContent>

          <TabsContent value="findings">
            <FindingsTab
              entities={entities}
              onRetry={() => onRetry("entities")}
              retryPending={retryPending}
              readOnly={readOnly}
            />
          </TabsContent>

          <TabsContent value="insights">
            <InsightsTab
              recommendations={recommendations}
              onRetry={() => onRetry("recommendations")}
              retryPending={retryPending}
              readOnly={readOnly}
            />
          </TabsContent>
        </Tabs>
      )}
    </aside>
  );
}

function ContentBadgeRow({
  aiGenerated,
  editedByDoctor,
}: {
  aiGenerated: boolean;
  editedByDoctor: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      {editedByDoctor ? (
        <Badge variant="outline">
          <Pencil className="mr-1 h-3 w-3" /> Doctor-edited
        </Badge>
      ) : aiGenerated ? (
        <Badge variant="default">
          <Sparkles className="mr-1 h-3 w-3" /> AI-generated
        </Badge>
      ) : null}
    </div>
  );
}

function SoapTab({
  soap,
  readOnly,
  onSave,
  saving,
  onRetry,
  retryPending,
}: {
  soap: SoapNote | null;
  readOnly: boolean;
  onSave: (payload: Record<string, string>) => void;
  saving: boolean;
  onRetry: () => void;
  retryPending: boolean;
}) {
  const [fields, setFields] = useState({
    subjective: soap?.subjective ?? "",
    objective: soap?.objective ?? "",
    assessment: soap?.assessment ?? "",
    plan: soap?.plan ?? "",
  });

  useEffect(() => {
    setFields({
      subjective: soap?.subjective ?? "",
      objective: soap?.objective ?? "",
      assessment: soap?.assessment ?? "",
      plan: soap?.plan ?? "",
    });
  }, [soap]);

  if (!soap) {
    return (
      <EmptyStageState
        label="SOAP note"
        onRetry={onRetry}
        retryPending={retryPending}
        readOnly={readOnly}
      />
    );
  }

  const dirty =
    fields.subjective !== (soap.subjective ?? "") ||
    fields.objective !== (soap.objective ?? "") ||
    fields.assessment !== (soap.assessment ?? "") ||
    fields.plan !== (soap.plan ?? "");

  return (
    <div className="flex flex-col gap-4 pt-4">
      <div className="flex items-center justify-between">
        <ContentBadgeRow aiGenerated={soap.ai_generated} editedByDoctor={soap.edited_by_doctor} />
        {!readOnly && (
          <Button variant="ghost" size="sm" onClick={onRetry} loading={retryPending}>
            <RotateCw className="h-3.5 w-3.5" /> Regenerate
          </Button>
        )}
      </div>
      {(
        [
          ["subjective", "Subjective"],
          ["objective", "Objective"],
          ["assessment", "AI Clinical Assessment"],
          ["plan", "Plan"],
        ] as const
      ).map(([key, label]) => (
        <div key={key} className="flex flex-col gap-1.5">
          <label className="text-caption font-medium text-text-secondary">{label}</label>
          <Textarea
            value={fields[key]}
            disabled={readOnly}
            onChange={(event) => setFields((prev) => ({ ...prev, [key]: event.target.value }))}
            rows={3}
          />
        </div>
      ))}
      {!readOnly && (
        <Button size="sm" onClick={() => onSave(fields)} disabled={!dirty} loading={saving}>
          Save changes
        </Button>
      )}
    </div>
  );
}

function SummaryTab({
  summary,
  readOnly,
  onSave,
  saving,
  onRetry,
  retryPending,
}: {
  summary: ClinicalSummary | null;
  readOnly: boolean;
  onSave: (payload: Record<string, string>) => void;
  saving: boolean;
  onRetry: () => void;
  retryPending: boolean;
}) {
  const [fields, setFields] = useState({
    chief_complaint: summary?.chief_complaint ?? "",
    history_of_present_illness: summary?.history_of_present_illness ?? "",
    key_findings: summary?.key_findings ?? "",
    assessment: summary?.assessment ?? "",
    plan: summary?.plan ?? "",
  });

  useEffect(() => {
    setFields({
      chief_complaint: summary?.chief_complaint ?? "",
      history_of_present_illness: summary?.history_of_present_illness ?? "",
      key_findings: summary?.key_findings ?? "",
      assessment: summary?.assessment ?? "",
      plan: summary?.plan ?? "",
    });
  }, [summary]);

  if (!summary) {
    return (
      <EmptyStageState
        label="clinical summary"
        onRetry={onRetry}
        retryPending={retryPending}
        readOnly={readOnly}
      />
    );
  }

  const dirty = (Object.keys(fields) as (keyof typeof fields)[]).some(
    (key) => fields[key] !== ((summary[key] as string | null) ?? ""),
  );

  return (
    <div className="flex flex-col gap-4 pt-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ContentBadgeRow aiGenerated editedByDoctor={summary.edited_by_doctor} />
          {summary.word_count != null && (
            <span className="text-caption text-text-secondary">{summary.word_count} words</span>
          )}
        </div>
        {!readOnly && (
          <Button variant="ghost" size="sm" onClick={onRetry} loading={retryPending}>
            <RotateCw className="h-3.5 w-3.5" /> Regenerate
          </Button>
        )}
      </div>
      {(
        [
          ["chief_complaint", "Chief complaint"],
          ["history_of_present_illness", "History of present illness"],
          ["key_findings", "Key findings"],
          ["assessment", "Assessment"],
          ["plan", "Plan"],
        ] as const
      ).map(([key, label]) => (
        <div key={key} className="flex flex-col gap-1.5">
          <label className="text-caption font-medium text-text-secondary">{label}</label>
          <Textarea
            value={fields[key]}
            disabled={readOnly}
            onChange={(event) => setFields((prev) => ({ ...prev, [key]: event.target.value }))}
            rows={2}
          />
        </div>
      ))}
      {!readOnly && (
        <Button size="sm" onClick={() => onSave(fields)} disabled={!dirty} loading={saving}>
          Save changes
        </Button>
      )}
    </div>
  );
}

function FindingsTab({
  entities,
  onRetry,
  retryPending,
  readOnly,
}: {
  entities: AiEntities | null;
  onRetry: () => void;
  retryPending: boolean;
  readOnly: boolean;
}) {
  if (!entities) {
    return (
      <EmptyStageState
        label="extracted findings"
        onRetry={onRetry}
        retryPending={retryPending}
        readOnly={readOnly}
      />
    );
  }

  const groups: [string, AiEntities["symptoms"]][] = [
    ["Symptoms", entities.symptoms],
    ["Medications", entities.medications],
    ["Allergies", entities.allergies],
    ["Medical history", entities.medical_history],
  ];

  return (
    <div className="flex flex-col gap-4 pt-4">
      <div className="flex items-center justify-between">
        <ConfidenceBadge level={entities.extraction_confidence} />
        {!readOnly && (
          <Button variant="ghost" size="sm" onClick={onRetry} loading={retryPending}>
            <RotateCw className="h-3.5 w-3.5" /> Re-extract
          </Button>
        )}
      </div>

      {entities.vitals && (
        <div className="flex flex-col gap-1.5">
          <span className="text-caption font-medium text-text-secondary">Vitals</span>
          <div className="flex flex-wrap gap-2">
            {Object.entries(entities.vitals).map(([key, value]) => (
              <Badge key={key} variant="outline">
                {key.replace(/_/g, " ")}: {value}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {groups.map(([label, items]) => (
        <div key={label} className="flex flex-col gap-1.5">
          <span className="text-caption font-medium text-text-secondary">{label}</span>
          {items.length === 0 ? (
            <span className="text-caption text-text-secondary">None noted</span>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {items.map((item, index) => (
                <Badge
                  key={index}
                  variant={item.negated ? "outline" : "default"}
                  className="capitalize"
                >
                  {item.negated ? `No ${item.text}` : item.text}
                  {item.severity ? ` (${item.severity})` : ""}
                </Badge>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function InsightsTab({
  recommendations,
  onRetry,
  retryPending,
  readOnly,
}: {
  recommendations: AiRecommendation[];
  onRetry: () => void;
  retryPending: boolean;
  readOnly: boolean;
}) {
  if (recommendations.length === 0) {
    return (
      <EmptyStageState
        label="AI insights"
        onRetry={onRetry}
        retryPending={retryPending}
        readOnly={readOnly}
      />
    );
  }

  const redFlags = recommendations.filter((r) => r.is_red_flag);
  const diagnoses = recommendations.filter((r) => r.type === "possible_diagnosis");
  const tests = recommendations.filter((r) => r.type === "recommended_test");

  return (
    <div className="flex flex-col gap-4 pt-4">
      <div className="flex items-center justify-end">
        {!readOnly && (
          <Button variant="ghost" size="sm" onClick={onRetry} loading={retryPending}>
            <RotateCw className="h-3.5 w-3.5" /> Regenerate
          </Button>
        )}
      </div>

      {redFlags.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-caption font-medium text-danger">Red flags</span>
          {redFlags.map((item) => (
            <div key={item.id} className="rounded-md border border-danger/30 bg-danger/5 p-3">
              <div className="flex items-start gap-2">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-danger" />
                <div>
                  <p className="text-body font-medium text-text-primary">{item.content}</p>
                  {item.explanation && (
                    <p className="mt-1 text-caption text-text-secondary">{item.explanation}</p>
                  )}
                  <ConfidenceBadge level={item.confidence} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {diagnoses.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-caption font-medium text-text-secondary">
            AI Suggestions – Requires Doctor Review
          </span>
          {diagnoses.map((item) => (
            <RecommendationCard key={item.id} item={item} />
          ))}
        </div>
      )}

      {tests.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-caption font-medium text-text-secondary">Recommended tests</span>
          {tests.map((item) => (
            <RecommendationCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

function RecommendationCard({ item }: { item: AiRecommendation }) {
  return (
    <div className="rounded-md border border-border p-3">
      <p className="text-body text-text-primary">{item.content}</p>
      {item.explanation && (
        <p className="mt-1 text-caption text-text-secondary">{item.explanation}</p>
      )}
      <div className="mt-2">
        <ConfidenceBadge level={item.confidence} />
      </div>
    </div>
  );
}

function EmptyStageState({
  label,
  onRetry,
  retryPending,
  readOnly,
}: {
  label: string;
  onRetry: () => void;
  retryPending: boolean;
  readOnly: boolean;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border p-8 text-center">
      <Sparkles className="h-6 w-6 text-text-secondary" />
      <p className="text-body text-text-secondary">No {label} is available yet.</p>
      {!readOnly && (
        <Button variant="secondary" size="sm" onClick={onRetry} loading={retryPending}>
          <RotateCw className="h-3.5 w-3.5" /> Generate now
        </Button>
      )}
    </div>
  );
}
