"use client"

import { useEffect, useRef } from "react"
import { ArrowRight } from "lucide-react"

export function CTASection() {
  const sectionRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const elements = entry.target.querySelectorAll(".fade-in-element")
            elements.forEach((element, index) => {
              setTimeout(() => {
                element.classList.add("animate-fade-in-up")
              }, index * 200)
            })
          }
        })
      },
      { threshold: 0.1 },
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    return () => observer.disconnect()
  }, [])

  return (
    <section id="contact" ref={sectionRef} className="relative py-8 px-4 sm:px-6 lg:px-8 mb-32">
      <div className="relative max-w-4xl mx-auto">
        <div className="fade-in-element opacity-0 translate-y-8 transition-all duration-1000 ease-out text-center p-8 md:p-10 rounded-3xl border border-purple-500/20 bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-violet-500/10 backdrop-blur-xl">
          {/* Background glow effects */}
          <div className="absolute -top-24 -left-24 w-48 h-48 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
          
          <h3 className="text-2xl md:text-3xl lg:text-4xl font-bold text-white mb-6 text-balance leading-tight relative">
            Ready to{" "}
            <span className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
              Scale Your Startup
            </span>
            ?
          </h3>
          <p className="text-lg text-white/70 mb-8 max-w-2xl mx-auto leading-relaxed relative">
            Join hundreds of Tunisian entrepreneurs already using AI to validate ideas, streamline legal processes, and grow their businesses.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 relative">
            <button className="group inline-flex items-center gap-3 px-8 py-4 md:px-12 md:py-6 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white rounded-full font-semibold text-base md:text-lg transition-all duration-300 hover:scale-105 shadow-2xl shadow-purple-500/25">
              Start Free Trial
              <ArrowRight className="w-5 h-5 md:w-6 md:h-6 group-hover:translate-x-1 transition-transform duration-200" />
            </button>
            <button className="group inline-flex items-center gap-3 px-8 py-4 md:px-10 md:py-5 bg-transparent border border-purple-400/50 hover:bg-purple-500/10 text-white rounded-full font-medium text-base md:text-lg transition-all duration-300 hover:scale-105">
              Schedule Demo
            </button>
          </div>
          
          <p className="text-white/50 text-sm mt-6 relative">
            No credit card required. Start with our free plan today.
          </p>
        </div>
      </div>
    </section>
  )
}
