"use client"

import { useEffect, useRef } from "react"
import { TestimonialsColumn } from "@/components/ui/testimonials-column"

export function TestimonialsSection() {
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
              }, index * 300)
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

  const testimonials = [
    {
      text: "ScaleUp transformed how we validate our business model. The AI-powered BMC analysis identified gaps we never noticed before.",
      name: "Ahmed Ben Ali",
      role: "Founder, TunisTech",
    },
    {
      text: "The legal document analysis saved us weeks of manual review. Signature verification gave us confidence in our contracts.",
      name: "Fatima Mansour",
      role: "CEO, MedTech Tunisia",
    },
    {
      text: "From idea validation to legal compliance, ScaleUp became our go-to platform. Our startup grew 3x in the first year.",
      name: "Youssef Khelifi",
      role: "Co-founder, AgriTech TN",
    },
    {
      text: "The financial analysis tools helped us understand our burn rate and optimize spending. Invaluable for early-stage startups.",
      name: "Leila Trabelsi",
      role: "CFO, FinTech Sousse",
    },
    {
      text: "ScaleUp's AI consulting gave us investor-ready insights. We secured our seed round within 3 months of using the platform.",
      name: "Karim Bouazizi",
      role: "Founder, StartupCarthage",
    },
    {
      text: "The SRS generator streamlined our product development process. What used to take weeks now takes hours.",
      name: "Nour Gharbi",
      role: "CTO, InnovateTN",
    },
    {
      text: "As a first-time founder, ScaleUp's guidance was crucial. The platform made complex business processes accessible and clear.",
      name: "Sami Dridi",
      role: "Founder, EduTech Tunisia",
    },
    {
      text: "The marketing analysis feature helped us understand our audience better. Our campaign ROI improved by 150%.",
      name: "Rim Hamdi",
      role: "Marketing Director, RetailTN",
    },
  ]

  return (
    <section id="testimonials" ref={sectionRef} className="relative pt-16 pb-16 px-4 sm:px-6 lg:px-8">
      {/* Grid Background */}
      <div className="absolute inset-0 opacity-10">
        <div
          className="h-full w-full"
          style={{
            backgroundImage: `
            linear-gradient(rgba(168,85,247,0.2) 1px, transparent 1px),
            linear-gradient(90deg, rgba(168,85,247,0.2) 1px, transparent 1px)
          `,
            backgroundSize: "80px 80px",
          }}
        />
      </div>

      <div className="relative max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="text-center mb-16 md:mb-32">
          <div className="fade-in-element opacity-0 translate-y-8 transition-all duration-1000 ease-out inline-flex items-center gap-2 text-purple-300/60 text-sm font-medium tracking-wider uppercase mb-6">
            <div className="w-8 h-px bg-purple-400/30"></div>
            Success Stories
            <div className="w-8 h-px bg-purple-400/30"></div>
          </div>
          <h2 className="fade-in-element opacity-0 translate-y-8 transition-all duration-1000 ease-out text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-8 tracking-tight text-balance">
            Tunisian Startups{" "}
            <span className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
              We Empower
            </span>
          </h2>
          <p className="fade-in-element opacity-0 translate-y-8 transition-all duration-1000 ease-out text-xl text-white/70 max-w-2xl mx-auto leading-relaxed">
            Discover how entrepreneurs across Tunisia are transforming their businesses with AI-powered tools
          </p>
        </div>

        {/* Testimonials Carousel */}
        <div className="fade-in-element opacity-0 translate-y-8 transition-all duration-1000 ease-out relative flex justify-center items-center min-h-[600px] md:min-h-[800px] overflow-hidden">
          <div
            className="flex gap-8 max-w-6xl"
            style={{
              maskImage: "linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%)",
              WebkitMaskImage: "linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%)",
            }}
          >
            <TestimonialsColumn testimonials={testimonials.slice(0, 3)} duration={15} className="flex-1" />
            <TestimonialsColumn
              testimonials={testimonials.slice(2, 5)}
              duration={12}
              className="flex-1 hidden md:block"
            />
            <TestimonialsColumn
              testimonials={testimonials.slice(1, 4)}
              duration={18}
              className="flex-1 hidden lg:block"
            />
          </div>
        </div>
      </div>
    </section>
  )
}
