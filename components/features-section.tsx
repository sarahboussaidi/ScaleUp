"use client"

import { useEffect, useRef, useState } from "react"
import { FileText, BarChart3, Brain, Shield, Lightbulb, Layers } from "lucide-react"

const features = [
  {
    title: "AI Business Model Canvas",
    description:
      "Generate and digitize your Business Model Canvas with AI. Get intelligent analysis and suggestions for improvement.",
    icon: Layers,
    gradient: "from-purple-500 to-indigo-600",
  },
  {
    title: "BMC Quality Evaluation",
    description:
      "Upload your BMC and receive detailed feedback on each box. Benchmark against successful startups and identify gaps.",
    icon: BarChart3,
    gradient: "from-indigo-500 to-violet-600",
  },
  {
    title: "Legal Document Analysis",
    description:
      "Upload legal documents for AI-powered text extraction, summarization, key clause identification, and signature verification.",
    icon: FileText,
    gradient: "from-violet-500 to-purple-600",
  },
  {
    title: "Signature Authenticity",
    description:
      "Advanced AI detection to classify signatures as genuine or potentially forged. Secure your legal processes.",
    icon: Shield,
    gradient: "from-purple-500 to-pink-600",
  },
  {
    title: "AI-Powered Consulting",
    description:
      "Get intelligent business advice, market insights, and strategic recommendations powered by advanced AI models.",
    icon: Brain,
    gradient: "from-indigo-500 to-purple-600",
  },
  {
    title: "Growth Insights",
    description:
      "Receive actionable optimization suggestions and growth insights based on your business data and market trends.",
    icon: Lightbulb,
    gradient: "from-violet-500 to-indigo-600",
  },
]

export function FeaturesSection() {
  const sectionRef = useRef<HTMLElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
        }
      },
      {
        threshold: 0.1,
        rootMargin: "0px 0px -100px 0px",
      },
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    return () => {
      if (sectionRef.current) {
        observer.unobserve(sectionRef.current)
      }
    }
  }, [])

  return (
    <section id="features" ref={sectionRef} className="relative z-10">
      <div className="bg-white/5 backdrop-blur-xl rounded-t-[3rem] pt-16 sm:pt-24 pb-16 sm:pb-24 px-4 relative overflow-hidden border-t border-white/10">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-[0.02]">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `radial-gradient(circle at 1px 1px, rgb(255,255,255) 1px, transparent 0)`,
              backgroundSize: "24px 24px",
            }}
          ></div>
        </div>

        {/* Floating particles */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-purple-400/30 rounded-full animate-float"
              style={{
                left: `${20 + i * 15}%`,
                top: `${30 + (i % 3) * 20}%`,
                animationDelay: `${i * 0.5}s`,
                animationDuration: `${4 + i * 0.5}s`,
              }}
            ></div>
          ))}
        </div>

        <div className="max-w-7xl mx-auto relative">
          <div
            className={`text-center mb-12 sm:mb-20 transition-all duration-1000 ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
            }`}
          >
            <div className="inline-flex items-center px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm font-medium mb-6">
              <svg className="w-4 h-4 mr-2 text-purple-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
              Powerful AI Features
            </div>
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white text-balance mb-4 sm:mb-6">
              Everything You Need to{" "}
              <span className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
                Scale Your Startup
              </span>
            </h2>
            <p className="text-base sm:text-lg md:text-xl text-white/70 max-w-3xl mx-auto font-light leading-relaxed">
              From business model validation to legal assistance and intelligent consulting, 
              ScaleUp provides all the AI tools Tunisian entrepreneurs need to succeed.
            </p>
          </div>

          <div
            className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 transition-all duration-1000 delay-300 ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
          >
            {features.map((feature, index) => (
              <div
                key={index}
                className="group transition-all duration-500"
                style={{
                  transitionDelay: isVisible ? `${300 + index * 100}ms` : "0ms",
                }}
              >
                <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 sm:p-8 h-full border border-white/10 hover:border-purple-500/30 transition-all duration-500 hover:-translate-y-2 hover:bg-white/10">
                  {/* Icon */}
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>

                  <h3 className="text-xl sm:text-2xl font-bold text-white mb-4 group-hover:text-purple-300 transition-colors duration-300">
                    {feature.title}
                  </h3>

                  <p className="text-white/60 text-sm sm:text-base leading-relaxed">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
