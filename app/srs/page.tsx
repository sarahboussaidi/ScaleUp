"use client";

import { useState, useCallback, useEffect } from "react";
import type { ElementType } from "react";
import { GlassmorphismNav } from "@/components/glassmorphism-nav";
import Aurora from "@/components/Aurora";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import {
  FileCode,
  Sparkles,
  Loader2,
  Download,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  BookOpen,
  Upload,
  X,
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  FileText,
  BarChart3,
  Brain,
  Eye,
  FileJson,
  FileDown,
} from "lucide-react";

const SRS_API_BASE = "http://localhost:5000/api/srs"

type ScoreBlock = {
  score: number;
  feedback: string;
  points: string[];
};

type ReportFiles = {
  json?: string;
  markdown?: string;
  md?: string;
  docx?: string;
  pdf?: string;
};

interface SRSSection {
  id: string;
  title: string;
  icon: ElementType;
  content: string;
  subsections?: { title: string; content: string }[];
}

interface GeneratedSRS {
  projectName: string;
  version: string;
  date: string;
  sections: SRSSection[];
  markdown?: string;
  downloadFile?: string;
  generatedRequirementsCount?: number;
  xai?: any;
  raw?: any;
}

interface NormalizedEvaluationResult {
  raw: any;
  overallScore: number;
  overallLabel: string;
  completeness: ScoreBlock;
  clarity: ScoreBlock;
  consistency: ScoreBlock;
  testability: ScoreBlock;
  feasibility: ScoreBlock;
  recommendations: string[];
  reportFiles: ReportFiles | null;
  modelBasedEvaluation: any;
  uploadedVisualClassification: any;
  extractedText: string;
  xai: any;
}

export default function SRSPage() {
  const [activeTab, setActiveTab] = useState<"generate" | "evaluate">(
    "generate",
  );

  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [targetUsers, setTargetUsers] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedSRS, setGeneratedSRS] = useState<GeneratedSRS | null>(null);
  const [expandedSections, setExpandedSections] = useState<string[]>([]);
  const [expandedScoreDetails, setExpandedScoreDetails] = useState<string[]>([])
  const [copied, setCopied] = useState(false);

  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<NormalizedEvaluationResult | null>(null);
  const [evaluationReportFiles, setEvaluationReportFiles] = useState<ReportFiles | null>(null);
  const [srsText, setSrsText] = useState("");
  const [rewriteResults, setRewriteResults] = useState<any[]>([])
  const [isRewriting, setIsRewriting] = useState(false)
  const [filePreviewUrl, setFilePreviewUrl] = useState<string | null>(null)
  const [filePreviewType, setFilePreviewType] = useState<"image" | "pdf" | "other" | null>(null)


  useEffect(() => {
  if (!uploadedFile) {
    setFilePreviewUrl(null)
    setFilePreviewType(null)
    return
  }

  const url = URL.createObjectURL(uploadedFile)
  setFilePreviewUrl(url)

  const lowerName = uploadedFile.name.toLowerCase()

  if (
    uploadedFile.type.startsWith("image/") ||
    [".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"].some((ext) =>
      lowerName.endsWith(ext),
    )
  ) {
    setFilePreviewType("image")
  } else if (uploadedFile.type === "application/pdf" || lowerName.endsWith(".pdf")) {
    setFilePreviewType("pdf")
  } else {
    setFilePreviewType("other")
  }

  return () => {
    URL.revokeObjectURL(url)
  }
}, [uploadedFile])

  const asArray = (value: any): string[] => {
    if (!value) return [];
    if (Array.isArray(value)) return value.map((v) => String(v));
    return [String(value)];
  };

  const pickNumber = (...values: any[]) => {
    for (const value of values) {
      const n = Number(value);
      if (Number.isFinite(n)) return Math.round(n);
    }
    return 0;
  };


  const toggleScoreDetails = (key: string) => {
  setExpandedScoreDetails((prev) =>
    prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key],
  )
}

  const normalizeEvaluationResult = (data: any): NormalizedEvaluationResult => {
    const ruleEval =
      data?.rule_based_evaluation || data?.evaluation || data || {};
    const modelScore = data?.model_aware_score || {};
    const modelEval = data?.model_based_evaluation || null;

    const overallScore = pickNumber(
      modelScore.final_model_aware_score,
      ruleEval.overall_score,
      data?.overall_score,
      data?.overallScore,
    );

    const recommendations = asArray(
      data?.recommendations || ruleEval.recommendations,
    );

    const uploadedVision =
  data?.uploaded_visual_classification ||
  modelEval?.uploaded_vision ||
  null

const extractedText =
  data?.input_text ||
  data?.extracted_text ||
  data?.text ||
  ""
    return {
      raw: data,
      overallScore,
      overallLabel:
        modelScore.final_model_aware_label ||
        ruleEval.overall_label ||
        ruleEval.quality_label ||
        data?.overall_label ||
        "SRS_EVALUATED",
        uploadedVisualClassification: uploadedVision,extractedText,
      completeness: {
  score: pickNumber(
    ruleEval.completeness_score,
    data?.completeness_score,
  ),
  feedback: `Detected ${asArray(ruleEval.detected_sections).length || 0} standard SRS sections.`,
  points: [
    ...asArray(ruleEval.detected_sections).map(
      (section: string) => `Detected section: ${section}`,
    ),
    ...asArray(ruleEval.missing_sections).map(
      (section: string) => `Missing section: ${section}`,
    ),
  ],
},
      clarity: {
        score: pickNumber(ruleEval.clarity_score, data?.clarity_score),
        feedback: `Detected ${ruleEval.vague_terms_count ?? 0} vague or unclear terms.`,
        points:
          asArray(ruleEval.detected_vague_terms).length > 0
            ? [
                ...asArray(ruleEval.detected_vague_terms).map(
                  (item: any) =>
                    `Term "${item.term}" detected ${item.count} time(s).`,
              ),
              ...asArray(ruleEval.vague_term_contexts).map(
                (item: any) =>
                    `Context for "${item.term}": ${item.sentence}`,
             ),
          ]
         : ["No major clarity issue detected."],
     },
      consistency: {
        score: pickNumber(ruleEval.consistency_score, data?.consistency_score),
        feedback:
          "Consistency is estimated from duplicated or repeated requirement-like sentences.",
        points: [
          pickNumber(ruleEval.consistency_score) < 80
            ? "Possible repeated or conflicting requirements detected."
            : "No major consistency conflict detected.",
        ],
      },
      testability: {
        score: pickNumber(ruleEval.testability_score, data?.testability_score),
        feedback:
          "Testability is based on measurable constraints, numeric thresholds, and acceptance-oriented wording.",
        points: [
          "Add measurable acceptance criteria.",
          "Use numeric thresholds such as response time, availability percentage, or maximum delay.",
          "Make each requirement verifiable by a test case.",
        ],
      },
      feasibility: {
        score: pickNumber(ruleEval.feasibility_score, data?.feasibility_score),
        feedback:
          "Feasibility is estimated from technical complexity and project constraints.",
        points: [
          pickNumber(ruleEval.feasibility_score) < 75
            ? "Some requirements may need clarification before implementation."
            : "Most requirements appear feasible.",
        ],
      },
      recommendations: recommendations.length
        ? recommendations
        : [
            "Review ambiguous requirements detected by the model-aware evaluation.",
            "Improve low-quality requirements using the LLM rewriting outputs.",
            "Add measurable constraints and acceptance criteria.",
          ],
      reportFiles: data?.report_files || data?.reportFiles || null,
      modelBasedEvaluation: modelEval,
      xai: modelEval?.xai || data?.xai || null,
    };
  };

  const parseSRSMarkdownForDisplay = (markdown: string) => {
    const cleaned = markdown.replace(/\r\n/g, "\n").trim();
    const tocIndex = cleaned.toLowerCase().indexOf("table of contents");
    return tocIndex >= 0 ? cleaned.slice(tocIndex) : cleaned;
  };

  const generateSRS = async () => {
    if (!projectName.trim() || !projectDescription.trim()) return;

    setIsGenerating(true);
    setEvaluationResult(null);
    setEvaluationReportFiles(null);

    try {
      const response = await fetch(`${SRS_API_BASE}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_name: projectName,
          prepared_by: "Sarah Boussaidi",
          description: projectDescription,
          target_users: targetUsers,
          functional_needs: projectDescription,
          non_functional_needs:
            "security, performance, usability, reliability, maintainability",
          constraints:
            "The system should be accessible, secure, and easy to use.",
        }),
      });

      const data = await response.json();
      console.log("SRS generation response:", data);

      if (!response.ok || data.status === "error") {
        alert(data.message || "SRS generation failed.");
        return;
      }

      const markdown =
        data.markdown || data.srs_markdown || "SRS generated successfully.";

      const realSRS: GeneratedSRS = {
        projectName: data.project_name || projectName,
        version: "1.0.0",
        date: new Date().toLocaleDateString("en-US", {
          year: "numeric",
          month: "long",
          day: "numeric",
        }),
        markdown,
        downloadFile: data.download_file || data.package_file || data.docx_file,
        generatedRequirementsCount:
          data.generated_requirements_count || data.requirements_count,
        xai: data.xai,
        raw: data,
        sections: [
          {
            id: "generated-srs",
            title: "Generated Professional SRS",
            icon: BookOpen,
            content: parseSRSMarkdownForDisplay(markdown),
            subsections: [
              {
                title: "Generated Requirements",
                content: `${data.generated_requirements_count || data.requirements_count || 0} requirements generated.`,
              },
              {
                title: "Generation Method",
                content:
                  "This SRS was generated using the SRS backend, previous notebook outputs, RAG references, quality scoring, and XAI summaries.",
              },
              {
                title: "XAI Summary",
                content:
                  data.xai?.message ||
                  "RAG evidence and quality explanations were used to support the generated SRS.",
              },
            ],
          },
        ],
      };

      setGeneratedSRS(realSRS);
      setExpandedSections(realSRS.sections.map((s) => s.id));
    } catch (error) {
      console.error(error);
      alert(
        "Backend connection error. Make sure python app.py is running on http://localhost:5000.",
      );
    } finally {
      setIsGenerating(false);
    }
  };


  const rewriteRequirements = async () => {
  if (!evaluationResult?.raw) {
    alert("Evaluate an SRS first.")
    return
  }

  setIsRewriting(true)

  try {
    const text =
  evaluationResult.extractedText ||
  evaluationResult.raw?.input_text ||
  evaluationResult.raw?.extracted_text ||
  evaluationResult.raw?.text ||
  srsText ||
  generatedSRS?.markdown ||
  ""

    const response = await fetch(`${SRS_API_BASE}/rewrite`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    })

    const data = await response.json()

    if (!response.ok || data.status === "error") {
      alert(data.message || "Requirement rewriting failed.")
      return
    }

    setRewriteResults(Array.isArray(data.rewrites) ? data.rewrites : [])
  } catch (error) {
    console.error(error)
    alert("Backend connection error while rewriting requirements.")
  } finally {
    setIsRewriting(false)
  }
}

  const evaluateGeneratedSRS = async () => {
    if (!generatedSRS?.markdown) {
      alert("No generated SRS available to evaluate.");
      return;
    }

    setIsEvaluating(true);

    try {
      const response = await fetch(`${SRS_API_BASE}/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: generatedSRS.markdown }),
      });

      const data = await response.json();
      console.log("Generated SRS evaluation response:", data);

      if (!response.ok || data.status === "error") {
        alert(data.message || "Generated SRS evaluation failed.");
        return;
      }

      const normalized = normalizeEvaluationResult(data);
      setEvaluationResult(normalized);
      setEvaluationReportFiles(normalized.reportFiles);
      setActiveTab("evaluate");
    } catch (error) {
      console.error(error);
      alert(
        "Generated SRS evaluation display error. Backend is running, but the response format could not be displayed. Check the browser console.",
      );
    } finally {
      setIsEvaluating(false);
    }
  };

  const evaluateSRS = async () => {
  if (!uploadedFile && !srsText.trim()) return

  setIsEvaluating(true)
  setEvaluationResult(null)
  setEvaluationReportFiles(null)
  setRewriteResults([])

  try {
    let response: Response

    if (uploadedFile) {
      const formData = new FormData()
      formData.append("file", uploadedFile)

      response = await fetch(`${SRS_API_BASE}/evaluate`, {
        method: "POST",
        body: formData,
      })
    } else {
      response = await fetch(`${SRS_API_BASE}/evaluate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: srsText,
        }),
      })
    }

    const data = await response.json()
    console.log("SRS evaluation response:", data)

    if (!response.ok || data.status === "error") {
      alert(data.message || "SRS evaluation failed.")
      return
    }

    const normalized = normalizeEvaluationResult(data)

    setEvaluationResult(normalized)
    setEvaluationReportFiles(normalized.reportFiles)
  } catch (error) {
    console.error("SRS evaluation error:", error)
    alert("Evaluation failed. Check backend terminal and browser console.")
  } finally {
    setIsEvaluating(false)
  }
}


  const downloadEvaluationReport = (
  format: "json" | "markdown" | "pdf" = "json",) => {
  if (!evaluationReportFiles) {
    alert("No evaluation report available yet.")
    return
  }

  const filePath =
  format === "json"
    ? evaluationReportFiles.json
    : format === "pdf"
      ? evaluationReportFiles.pdf
      : evaluationReportFiles.markdown || evaluationReportFiles.md

  if (!filePath) {
    alert("Report file not found.")
    return
  }

  const url = `${SRS_API_BASE}/download-report?file=${encodeURIComponent(filePath)}`
  window.open(url, "_blank")
}

  const toggleSection = (id: string) => {
    setExpandedSections((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );
  };

  const copyToClipboard = () => {
    if (!generatedSRS) return;
    navigator.clipboard.writeText(
      generatedSRS.markdown ||
        generatedSRS.sections.map((s) => s.content).join("\n\n"),
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadSRS = () => {
    if (!generatedSRS) return;

    if (generatedSRS.downloadFile) {
      downloadBackendFile(generatedSRS.downloadFile);
      return;
    }

    const content =
      generatedSRS.markdown ||
      generatedSRS.sections.map((s) => s.content).join("\n\n");
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${generatedSRS.projectName.replace(/\s+/g, "_")}_SRS.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const isAcceptedSRSFile = (file: File) => {
  const name = file.name.toLowerCase()

  return (
    file.type === "application/pdf" ||
    file.type === "text/plain" ||
    file.type.startsWith("image/") ||
    name.endsWith(".md") ||
    name.endsWith(".txt") ||
    name.endsWith(".pdf") ||
    name.endsWith(".png") ||
    name.endsWith(".jpg") ||
    name.endsWith(".jpeg") ||
    name.endsWith(".webp") ||
    name.endsWith(".tif") ||
    name.endsWith(".tiff")
  )
}

  const acceptFile = (file: File) => {
  if (!isAcceptedSRSFile(file)) {
    alert("Please upload a PDF, TXT, MD, or image file.")
    return
  }

  setUploadedFile(file)
  setEvaluationResult(null)
  setEvaluationReportFiles(null)

  const name = file.name.toLowerCase()

  if (
    file.type === "text/plain" ||
    name.endsWith(".md") ||
    name.endsWith(".txt")
  ) {
    const reader = new FileReader()
    reader.onload = (e) => {
      setSrsText((e.target?.result as string) || "")
    }
    reader.readAsText(file)
  } else {
    setSrsText("")
  }
}

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) acceptFile(droppedFile);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) acceptFile(selectedFile);
  };

  const clearUpload = () => {
    setUploadedFile(null);
    setSrsText("");
    setEvaluationResult(null);
    setEvaluationReportFiles(null);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-yellow-400";
    return "text-red-400";
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return "bg-green-500/20 border-green-500/30";
    if (score >= 60) return "bg-yellow-500/20 border-yellow-500/30";
    return "bg-red-500/20 border-red-500/30";
  };

  const getScoreIcon = (score: number) => {
    if (score >= 80) return CheckCircle;
    if (score >= 60) return AlertCircle;
    return AlertTriangle;
  };

  const modelDistribution = (path: any) => JSON.stringify(path || {}, null, 2);

  const renderSRSContent = (content: string) => {
    return content
      .split("\n")
      .filter((line, index, arr) => line.trim() || arr[index - 1]?.trim())
      .map((line, index) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={index} className="h-3" />;
        if (trimmed.startsWith("# ")) {
          return (
            <h2 key={index} className="text-2xl font-bold text-white mt-4 mb-4">
              {trimmed.replace(/^#\s*/, "")}
            </h2>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h3
              key={index}
              className="text-xl font-bold text-purple-300 mt-6 mb-3"
            >
              {trimmed.replace(/^##\s*/, "")}
            </h3>
          );
        }
        if (trimmed.startsWith("### ")) {
          return (
            <h4
              key={index}
              className="text-lg font-semibold text-indigo-300 mt-4 mb-2"
            >
              {trimmed.replace(/^###\s*/, "")}
            </h4>
          );
        }
        if (
          /^\d+\./.test(trimmed) ||
          trimmed.startsWith("-") ||
          trimmed.startsWith("•")
        ) {
          return (
            <p
              key={index}
              className="text-white/75 text-sm leading-relaxed ml-4 mb-2"
            >
              {trimmed}
            </p>
          );
        }
        return (
          <p key={index} className="text-white/75 text-sm leading-relaxed mb-2">
            {trimmed.replace(/\*\*/g, "")}
          </p>
        );
      });
  };

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      <main className="min-h-screen relative overflow-hidden">
        <div className="fixed inset-0 w-full h-full">
          <Aurora
            colorStops={["#1e1b4b", "#4c1d95", "#312e81"]}
            amplitude={1.2}
            blend={0.6}
            speed={0.8}
          />
        </div>

        <div className="relative z-10">
          <GlassmorphismNav />

          <section className="pt-32 pb-16 px-4">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-8">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-6">
                  <FileCode className="w-4 h-4 mr-2" />
                  SRS Generator & Evaluator
                </div>
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
                  AI-Powered{" "}
                  <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                    SRS Tools
                  </span>
                </h1>
                <p className="text-lg text-white/70 max-w-2xl mx-auto">
                  Generate Software Requirements Specifications and evaluate
                  them using rule-based checks, notebook outputs, NLP models, CV
                  signals, and XAI summaries.
                </p>
              </div>

              <div className="flex justify-center mb-8">
                <div className="flex gap-2 p-1 bg-white/5 backdrop-blur-xl rounded-xl border border-white/10">
                  <button
                    onClick={() => setActiveTab("generate")}
                    className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
                      activeTab === "generate"
                        ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
                        : "text-white/60 hover:text-white hover:bg-white/10"
                    }`}
                  >
                    <Sparkles className="w-4 h-4" />
                    Generate SRS
                  </button>
                  <button
                    onClick={() => setActiveTab("evaluate")}
                    className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
                      activeTab === "evaluate"
                        ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
                        : "text-white/60 hover:text-white hover:bg-white/10"
                    }`}
                  >
                    <BarChart3 className="w-4 h-4" />
                    Evaluate SRS
                  </button>
                </div>
              </div>

              {activeTab === "generate" ? (
                <>
                  {!generatedSRS ? (
                    <Card className="bg-white/5 backdrop-blur-xl border-white/10 max-w-2xl mx-auto">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <Sparkles className="w-5 h-5 text-indigo-400" />
                          Project Details
                        </CardTitle>
                        <CardDescription className="text-white/60">
                          Enter your project information to generate an SRS
                          document.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <label className="text-white/70 text-sm mb-2 block">
                            Project Name *
                          </label>
                          <Input
                            placeholder="e.g., Smart City Waste Management System"
                            value={projectName}
                            onChange={(e) => setProjectName(e.target.value)}
                            className="bg-white/5 border-white/10 text-white placeholder:text-white/40"
                          />
                        </div>
                        <div>
                          <label className="text-white/70 text-sm mb-2 block">
                            Project Description *
                          </label>
                          <Textarea
                            placeholder="Describe what your project does, its users, main functions, constraints, and expected outputs."
                            value={projectDescription}
                            onChange={(e) =>
                              setProjectDescription(e.target.value)
                            }
                            className="bg-white/5 border-white/10 text-white placeholder:text-white/40 min-h-[140px]"
                          />
                        </div>
                        <div>
                          <label className="text-white/70 text-sm mb-2 block">
                            Target Users (optional)
                          </label>
                          <Textarea
                            placeholder="e.g., administrators, citizens, operators, managers"
                            value={targetUsers}
                            onChange={(e) => setTargetUsers(e.target.value)}
                            className="bg-white/5 border-white/10 text-white placeholder:text-white/40 min-h-[80px]"
                          />
                        </div>
                        <Button
                          onClick={generateSRS}
                          disabled={
                            isGenerating ||
                            !projectName.trim() ||
                            !projectDescription.trim()
                          }
                          className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                        >
                          {isGenerating ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Generating SRS Document...
                            </>
                          ) : (
                            <>
                              <FileCode className="w-4 h-4 mr-2" />
                              Generate SRS
                            </>
                          )}
                        </Button>
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="space-y-6">
                      <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                        <CardContent className="p-6">
                          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                            <div>
                              <h2 className="text-2xl font-bold text-white mb-1">
                                {generatedSRS.projectName}
                              </h2>
                              <p className="text-white/60 text-sm">
                                Version {generatedSRS.version} | Generated on{" "}
                                {generatedSRS.date}
                              </p>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={copyToClipboard}
                                className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                              >
                                {copied ? (
                                  <Check className="w-4 h-4 mr-2" />
                                ) : (
                                  <Copy className="w-4 h-4 mr-2" />
                                )}
                                {copied ? "Copied" : "Copy"}
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={downloadSRS}
                                className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                              >
                                <Download className="w-4 h-4 mr-2" />
                                Download SRS
                              </Button>
                              <Button
                                size="sm"
                                onClick={evaluateGeneratedSRS}
                                disabled={isEvaluating}
                                className="bg-emerald-600 hover:bg-emerald-700 text-white"
                              >
                                {isEvaluating ? (
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                ) : (
                                  <BarChart3 className="w-4 h-4 mr-2" />
                                )}
                                Evaluate Generated SRS
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => setGeneratedSRS(null)}
                                className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
                              >
                                New SRS
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      <div className="space-y-4">
                        {generatedSRS.sections.map((section) => (
                          <Card
                            key={section.id}
                            className="bg-white/5 backdrop-blur-xl border-white/10 overflow-hidden"
                          >
                            <button
                              onClick={() => toggleSection(section.id)}
                              className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors"
                            >
                              <div className="flex items-center gap-3">
                                <section.icon className="w-5 h-5 text-indigo-400" />
                                <span className="text-white font-medium">
                                  {section.title}
                                </span>
                              </div>
                              {expandedSections.includes(section.id) ? (
                                <ChevronDown className="w-5 h-5 text-white/60" />
                              ) : (
                                <ChevronRight className="w-5 h-5 text-white/60" />
                              )}
                            </button>
                            {expandedSections.includes(section.id) && (
                              <CardContent className="pt-0 px-4 pb-4">
                                <div className="max-h-[620px] overflow-y-auto rounded-xl border border-white/10 bg-black/30 p-6">
                                  {renderSRSContent(section.content)}
                                </div>
                                {section.subsections && (
                                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                                    {section.subsections.map((sub, index) => (
                                      <div
                                        key={index}
                                        className="p-4 bg-white/5 rounded-lg border border-white/10"
                                      >
                                        <h4 className="text-white font-medium mb-2">
                                          {sub.title}
                                        </h4>
                                        <p className="text-white/60 text-sm whitespace-pre-line">
                                          {sub.content}
                                        </p>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </CardContent>
                            )}
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="space-y-6">
                  <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Upload className="w-5 h-5 text-indigo-400" />
                        Upload or Paste Your SRS
                      </CardTitle>
                      <CardDescription className="text-white/60">
                        Upload a PNG/PDF/TXT/MD SRS document or paste SRS content to
                        evaluate quality using your model-aware backend.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {!uploadedFile ? (
                        <>
                          <div
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                              isDragging
                                ? "border-indigo-400 bg-indigo-500/10"
                                : "border-white/20 bg-white/5 hover:bg-white/10"
                            }`}
                          >
                            <Upload className="w-10 h-10 text-indigo-400 mx-auto mb-3" />
                            <p className="text-white font-medium mb-2">
                              Drop your SRS file here
                            </p>
                            <p className="text-white/50 text-sm mb-4">
                              PDF, TXT, or Markdown,or image file
                            </p>
                            <label className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer transition">
                              Choose File
                              <input
                                type="file"
                                accept=".pdf,.txt,.md,.png,.jpg,.jpeg,.webp,.tif,.tiff,image/*"
                                onChange={handleFileSelect}
                                className="hidden"
                              />
                            </label>
                          </div>

                          <div>
                            <label className="text-white/70 text-sm mb-2 block">
                              Or paste SRS text
                            </label>
                            <Textarea
                              placeholder="Paste SRS content here..."
                              value={srsText}
                              onChange={(e) => {
                                setSrsText(e.target.value);
                                setEvaluationResult(null);
                                setEvaluationReportFiles(null);
                              }}
                              className="bg-white/5 border-white/10 text-white placeholder:text-white/40 min-h-[180px]"
                            />
                          </div>

                          {srsText.trim() && (
                            <Button
                              onClick={evaluateSRS}
                              disabled={isEvaluating}
                              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                            >
                              {isEvaluating ? (
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              ) : (
                                <BarChart3 className="w-4 h-4 mr-2" />
                              )}
                              {isEvaluating ? "Evaluating..." : "Evaluate SRS"}
                            </Button>
                          )}
                        </>
                      ) : (
                        <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10">
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                              <FileText className="w-6 h-6 text-indigo-400" />
                            </div>
                            <div>
                              <p className="text-white font-medium">
                                {uploadedFile.name}
                              </p>
                              <p className="text-white/50 text-sm">
                                {(uploadedFile.size / 1024).toFixed(1)} KB
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            {!evaluationResult && (
                              <Button
                                onClick={evaluateSRS}
                                disabled={isEvaluating}
                                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                              >
                                {isEvaluating ? (
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                ) : (
                                  <BarChart3 className="w-4 h-4 mr-2" />
                                )}
                                {isEvaluating ? "Evaluating..." : "Evaluate"}
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={clearUpload}
                              className="text-white/60 hover:text-white hover:bg-white/10"
                            >
                              <X className="w-5 h-5" />
                            </Button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {evaluationResult && (
                    <div className="space-y-6">
                      <Card
                        className={`border ${getScoreBg(evaluationResult.overallScore)}`}
                      >
                        <CardContent className="p-6">
                          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                            <div>
                              <p className="text-white/60 text-sm mb-1">
                                Overall SRS Quality Score
                              </p>
                              <p
                                className={`text-4xl font-bold ${getScoreColor(evaluationResult.overallScore)}`}
                              >
                                {evaluationResult.overallScore}/100
                              </p>
                              <p className="text-white/50 text-sm mt-1">
                                {evaluationResult.overallLabel}
                              </p>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {evaluationReportFiles && (
                                <>
                                <Button
                                   onClick={() => downloadEvaluationReport("json")}
                                   className="bg-emerald-600 hover:bg-emerald-700 text-white"
                                >
                                  <FileJson className="w-4 h-4 mr-2" />
                                  Download JSON Report
                                </Button>
                                
                                <Button
                                onClick={() => downloadEvaluationReport("markdown")}
                                className="bg-violet-600 hover:bg-violet-700 text-white"
                                >
                                  <FileDown className="w-4 h-4 mr-2" />
                                  Download Markdown Report
                                </Button>
                                 <Button
                                 onClick={() => downloadEvaluationReport("pdf")}
                                 className="bg-blue-600 hover:bg-blue-700 text-white"
                               >
                                 <Download className="w-4 h-4 mr-2" />
                                    Download PDF Report
                                </Button>
                              </>
                            )}
                              <div
                                className={`w-20 h-20 rounded-full border-4 flex items-center justify-center ${
                                  evaluationResult.overallScore >= 80
                                    ? "border-green-400"
                                    : evaluationResult.overallScore >= 60
                                      ? "border-yellow-400"
                                      : "border-red-400"
                                }`}
                              >
                                {(() => {
                                  const Icon = getScoreIcon(
                                    evaluationResult.overallScore,
                                  );
                                  return (
                                    <Icon
                                      className={`w-9 h-9 ${getScoreColor(evaluationResult.overallScore)}`}
                                    />
                                  );
                                })()}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {evaluationResult && (
  <Card className="overflow-hidden border border-emerald-400/20 bg-gradient-to-br from-emerald-500/10 via-purple-500/10 to-black/40 backdrop-blur-xl shadow-2xl">
    <CardHeader>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <CardTitle className="text-white flex items-center gap-2">
            <Eye className="w-5 h-5 text-emerald-300" />
            Uploaded Document Intelligence
          </CardTitle>
          <CardDescription className="text-white/60">
            OCR extraction, scanned-document analysis, and current-file ResNet/CV page classification.
          </CardDescription>
        </div>

        {evaluationResult.uploadedVisualClassification && (
          <div className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-4 py-2 text-emerald-200 text-sm font-semibold">
            {evaluationResult.uploadedVisualClassification.resnet_status === "trained_resnet_loaded"
  ? "Image classifier active"
  : "Visual fallback active"}
          </div>
        )}
      </div>
    </CardHeader>

    <CardContent className="grid grid-cols-1 xl:grid-cols-3 gap-5">
  <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
    <div className="mb-3">
      <h4 className="text-white font-semibold">Uploaded File Preview</h4>
      <p className="text-white/50 text-xs">
        Visual preview of the PDF or image submitted for analysis.
      </p>
    </div>

    <div className="h-[520px] overflow-hidden rounded-xl border border-white/10 bg-black/40 flex items-center justify-center">
      {filePreviewUrl && filePreviewType === "image" && (
        <img
          src={filePreviewUrl}
          alt="Uploaded SRS preview"
          className="h-full w-full object-contain"
        />
      )}

      {filePreviewUrl && filePreviewType === "pdf" && (
        <iframe
          src={filePreviewUrl}
          title="Uploaded PDF preview"
          className="h-full w-full bg-white"
        />
      )}

      {filePreviewUrl && filePreviewType === "other" && (
        <div className="text-center px-4">
          <FileText className="w-10 h-10 mx-auto text-indigo-300 mb-3" />
          <p className="text-white font-medium">{uploadedFile?.name}</p>
          <p className="text-white/50 text-xs mt-1">
            Preview is available for PDF and image files.
          </p>
        </div>
      )}

      {!filePreviewUrl && (
        <div className="text-center px-4">
          <FileText className="w-10 h-10 mx-auto text-indigo-300 mb-3" />
          <p className="text-white/60 text-sm">
            No uploaded file preview available.
          </p>
        </div>
      )}
    </div>
  </div>

  <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
    <div className="flex items-center justify-between mb-3">
      <div>
        <h4 className="text-white font-semibold">Extracted Text</h4>
        <p className="text-white/50 text-xs">
          Raw OCR/text extracted from the uploaded document.
        </p>
      </div>

      <Button
        size="sm"
        variant="outline"
        className="bg-white/5 border-white/20 text-white hover:bg-white/10"
        onClick={() =>
          navigator.clipboard.writeText(evaluationResult.extractedText || "")
        }
      >
        <Copy className="w-4 h-4 mr-2" />
        Copy
      </Button>
    </div>

    <div className="max-h-[520px] overflow-y-auto rounded-xl border border-white/10 bg-black/40 p-4">
      <pre className="whitespace-pre-wrap text-xs leading-relaxed text-white/75">
        {evaluationResult.extractedText || "No extracted text available."}
      </pre>
    </div>
  </div>

  <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-5">
    <h4 className="text-white font-semibold mb-1">
      Current File ResNet/CV Classification
    </h4>
    <p className="text-white/50 text-xs mb-4">
      Prediction for the PDF/image you uploaded, not only notebook statistics.
    </p>

    {evaluationResult.uploadedVisualClassification ? (
      <>
        <div className="rounded-2xl bg-black/30 border border-white/10 p-5 mb-4">
          <p className="text-white/50 text-sm">Predicted document type</p>
          <p className="text-3xl font-bold text-emerald-300 mt-1">
            {evaluationResult.uploadedVisualClassification.overall_uploaded_document_type_display ||
              evaluationResult.uploadedVisualClassification.overall_uploaded_document_type ||
              "Unknown"}
          </p>

          <div className="grid grid-cols-2 gap-3 mt-5">
            <div className="rounded-xl bg-white/5 p-3">
              <p className="text-white/40 text-xs">Confidence</p>
              <p className="text-white font-semibold">
                {evaluationResult.uploadedVisualClassification.confidence
                  ? `${Math.round(
                      Number(evaluationResult.uploadedVisualClassification.confidence) * 100,
                    )}%`
                  : "N/A"}
              </p>
            </div>

            <div className="rounded-xl bg-white/5 p-3">
              <p className="text-white/40 text-xs">Model</p>
              <p className="text-white font-semibold">
                {evaluationResult.uploadedVisualClassification.resnet_status ===
                "trained_resnet_loaded"
                  ? "ResNet18 classifier"
                  : "OCR visual fallback"}
              </p>
            </div>
          </div>
        </div>

        {evaluationResult.uploadedVisualClassification.page_predictions?.length > 0 && (
          <div className="space-y-2">
            <p className="text-white/70 text-sm font-medium">
              Page-level predictions
            </p>

            {evaluationResult.uploadedVisualClassification.page_predictions.map(
              (page: any, index: number) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-xl bg-black/30 border border-white/10 px-4 py-3 text-sm"
                >
                  <span className="text-white/70">Page {page.page_number}</span>
                  <span className="font-semibold text-emerald-300">
                    {page.display_page_type || page.predicted_page_type}
                  </span>
                  <span className="text-white/50">
                    {page.confidence
                      ? `${Math.round(Number(page.confidence) * 100)}%`
                      : "N/A"}
                  </span>
                </div>
              ),
            )}
          </div>
        )}
      </>
    ) : (
      <div className="rounded-xl bg-black/30 p-4 text-white/60 text-sm">
        No current-file ResNet/CV classification found in backend response.
      </div>
    )}
  </div>
</CardContent>
  </Card>
)}

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  {[
    { key: "completeness", title: "Completeness", data: evaluationResult.completeness },
    { key: "clarity", title: "Clarity", data: evaluationResult.clarity },
    { key: "consistency", title: "Consistency", data: evaluationResult.consistency },
    { key: "testability", title: "Testability", data: evaluationResult.testability },
    { key: "feasibility", title: "Feasibility", data: evaluationResult.feasibility },
  ].map((item) => {
    const points = Array.isArray(item.data?.points) ? item.data.points : []
    const isOpen = expandedScoreDetails.includes(item.key)

    return (
      <Card key={item.key} className="bg-white/5 backdrop-blur-xl border-white/10">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-white font-medium">{item.title}</span>
            <span className={`font-bold text-lg ${getScoreColor(item.data.score)}`}>
              {item.data.score}%
            </span>
          </div>

          <div className="w-full bg-white/10 rounded-full h-2 mb-3">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${
                item.data.score >= 80
                  ? "bg-green-400"
                  : item.data.score >= 60
                    ? "bg-yellow-400"
                    : "bg-red-400"
              }`}
              style={{ width: `${item.data.score}%` }}
            />
          </div>

          <p className="text-white/60 text-sm mb-3">
            {item.data.feedback}
          </p>

          {points.length > 0 && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => toggleScoreDetails(item.key)}
              className="bg-white/5 border-white/20 text-white hover:bg-white/10"
            >
              {isOpen ? "Hide details" : "See details"}
            </Button>
          )}

          {isOpen && points.length > 0 && (
            <div className="mt-4 space-y-2">
              {points.map((point: string, i: number) => (
                <p
                  key={i}
                  className="text-white/60 text-xs flex items-start gap-2"
                >
                  <span className="text-indigo-300">•</span>
                  <span>{point}</span>
                </p>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    )
  })}
</div>

                      

                      <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                        <CardHeader>
                          <CardTitle className="text-white flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-indigo-400" />
                            Recommendations for Improvement
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="flex justify-end mb-4">
  <Button
    onClick={rewriteRequirements}
    disabled={isRewriting}
    className="bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white"
  >
    {isRewriting ? (
      <>
        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
        Rewriting...
      </>
    ) : (
      <>
        <Sparkles className="w-4 h-4 mr-2" />
        LLM Rewrite Weak Requirements
      </>
    )}
  </Button>
</div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {evaluationResult.recommendations.map(
                              (rec, index) => (
                                <div
                                  key={index}
                                  className="flex items-start gap-3 p-3 bg-white/5 rounded-lg border border-white/10"
                                >
                                  <div className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                    <span className="text-indigo-400 text-xs font-bold">
                                      {index + 1}
                                    </span>
                                  </div>
                                  <span className="text-white/70 text-sm">
                                    {rec}
                                  </span>
                                </div>
                              ),
                            )}
                          </div>
                        </CardContent>
                      </Card>
                      {rewriteResults.length > 0 && (
  <Card className="bg-white/5 border-white/10 mt-6">
    <CardHeader>
      <CardTitle className="text-white flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-pink-300" />
        LLM Requirement Rewriting Results
      </CardTitle>
      <CardDescription className="text-white/60">
        Weak or ambiguous requirements detected in the uploaded document and rewritten into clearer SRS requirements.
      </CardDescription>
    </CardHeader>

    <CardContent className="space-y-4">
      {rewriteResults.slice(0, 10).map((item, index) => (
        <div
          key={index}
          className="p-4 rounded-xl bg-black/30 border border-white/10 space-y-2"
        >
          <p className="text-red-300 text-sm font-semibold">
            Original
          </p>
          <p className="text-white/60 text-sm">
            {item.original}
          </p>

          <p className="text-green-300 text-sm font-semibold">
            Improved
          </p>
          <p className="text-white/80 text-sm">
            {item.rewritten}
          </p>

          <p className="text-white/40 text-xs">
            {item.reason && (
  <p className="text-white/40 text-xs">
    Reason: {item.reason}
  </p>
)}
          </p>
        </div>
      ))}
    </CardContent>
  </Card>
)}

                      <div className="flex justify-center gap-4">
                        <Button
                          onClick={clearUpload}
                          variant="outline"
                          className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                        >
                          Evaluate Another SRS
                        </Button>
                        <Button
                          onClick={() => setActiveTab("generate")}
                          className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                        >
                          Generate New SRS
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>

          <Footer />
        </div>
      </main>
    </div>
  );
}