"use client"

import { useEffect, useRef, useState } from "react"
import { Check } from "lucide-react"
import { Button } from "@/components/ui/button"

const plans = [
  {
    name: "Free",
    price: "0",
    description: "Perfect for exploring our platform",
    features: [
      "5 document analyses per month",
      "Basic BMC generation",
      "Community support",
      "Limited AI consultations",
    ],
    cta: "Get Started Free",
    popular: false,
  },
  {
    name: "Startup",
    price: "49",
    description: "Ideal for growing startups",
    features: [
      "Unlimited document analyses",
      "Advanced BMC tools",
      "Signature verification",
      "Priority support",
      "Financial analysis tools",
      "Legal document classification",
    ],
    cta: "Start Startup Plan",
    popular: true,
  },
  {
    name: "Enterprise",
    price: "199",
    description: "For established businesses",
    features: [
      "Everything in Startup",
      "Custom AI training",
      "Dedicated account manager",
      "API access",
      "White-label options",
      "Advanced analytics",
      "Compliance reporting",
    ],
    cta: "Contact Sales",
    popular: false,
  },
]

export function PricingSection() {
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
    <section id="pricing" ref={sectionRef} className="relative z-10 py-16 sm:py-24 px-4">
      <div className="max-w-7xl mx-auto">
        <div
          className={`text-center mb-12 sm:mb-20 transition-all duration-1000 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-sm font-medium mb-6">
            <svg className="w-4 h-4 mr-2 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Simple Pricing
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white text-balance mb-4 sm:mb-6">
            Choose Your{" "}
            <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
              Growth Plan
            </span>
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-white/70 max-w-3xl mx-auto font-light leading-relaxed">
            Start free and scale as your startup grows. All plans include our core AI features.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative transition-all duration-700 ${
                isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
              }`}
              style={{
                transitionDelay: isVisible ? `${300 + index * 150}ms` : "0ms",
              }}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full text-white text-sm font-medium">
                  Most Popular
                </div>
              )}
              <div
                className={`h-full rounded-2xl p-6 sm:p-8 border transition-all duration-300 hover:-translate-y-2 ${
                  plan.popular
                    ? "bg-gradient-to-b from-purple-500/20 to-indigo-500/10 border-purple-500/30"
                    : "bg-white/5 backdrop-blur-md border-white/10 hover:border-purple-500/30"
                }`}
              >
                <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                <p className="text-white/60 text-sm mb-6">{plan.description}</p>

                <div className="flex items-baseline mb-6">
                  <span className="text-4xl font-bold text-white">${plan.price}</span>
                  <span className="text-white/60 ml-2">/month</span>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start gap-3">
                      <div className="w-5 h-5 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Check className="w-3 h-3 text-purple-400" />
                      </div>
                      <span className="text-white/70 text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  className={`w-full rounded-xl py-3 font-medium transition-all duration-300 ${
                    plan.popular
                      ? "bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white"
                      : "bg-white/10 hover:bg-white/20 text-white border border-white/20"
                  }`}
                >
                  {plan.cta}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
