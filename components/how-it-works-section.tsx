"use client"

import { useEffect, useRef, useState } from "react"
import { Upload, Brain, Lightbulb, Shield, TrendingUp } from "lucide-react"

const steps = [
  {
    number: "01",
    title: "Upload Data",
    description: "Upload your business documents, BMC, legal papers, or financial data to our secure platform.",
    icon: Upload,
  },
  {
    number: "02",
    title: "AI Analysis",
    description: "Our advanced AI processes your data, extracting insights and identifying key patterns.",
    icon: Brain,
  },
  {
    number: "03",
    title: "Optimization Suggestions",
    description: "Receive actionable recommendations to improve your business model and operations.",
    icon: Lightbulb,
  },
  {
    number: "04",
    title: "Legal Verification",
    description: "Verify documents, signatures, and ensure compliance with Tunisian regulations.",
    icon: Shield,
  },
  {
    number: "05",
    title: "Growth Insights",
    description: "Get data-driven insights to scale your startup and achieve sustainable growth.",
    icon: TrendingUp,
  },
]

export function HowItWorksSection() {
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
    <section id="how-it-works" ref={sectionRef} className="relative z-10 py-16 sm:py-24 px-4">
      <div className="max-w-7xl mx-auto">
        <div
          className={`text-center mb-12 sm:mb-20 transition-all duration-1000 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-6">
            <svg className="w-4 h-4 mr-2 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Simple Process
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white text-balance mb-4 sm:mb-6">
            How{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              ScaleUp Works
            </span>
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-white/70 max-w-3xl mx-auto font-light leading-relaxed">
            A streamlined workflow designed to transform your startup from idea to success
          </p>
        </div>

        <div className="relative">
          {/* Connection line */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-purple-500/30 to-transparent -translate-y-1/2" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
            {steps.map((step, index) => (
              <div
                key={index}
                className={`relative transition-all duration-700 ${
                  isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
                }`}
                style={{
                  transitionDelay: isVisible ? `${300 + index * 150}ms` : "0ms",
                }}
              >
                <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 hover:border-purple-500/30 transition-all duration-300 hover:-translate-y-2 h-full">
                  {/* Step number */}
                  <div className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent mb-4">
                    {step.number}
                  </div>

                  {/* Icon */}
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-purple-500/20 to-indigo-500/20 flex items-center justify-center mb-4 border border-purple-500/20">
                    <step.icon className="w-6 h-6 text-purple-400" />
                  </div>

                  <h3 className="text-lg font-bold text-white mb-2">{step.title}</h3>
                  <p className="text-white/60 text-sm leading-relaxed">{step.description}</p>
                </div>

                {/* Arrow connector for larger screens */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-3 -translate-y-1/2 z-10">
                    <div className="w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center border border-purple-500/30">
                      <svg className="w-3 h-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
