"use client"
import type React from "react"
import type { ComponentProps, ReactNode } from "react"
import { motion, useReducedMotion } from "framer-motion"
import { FacebookIcon, InstagramIcon, LinkedinIcon, TwitterIcon } from "lucide-react"
import Image from "next/image"

interface FooterLink {
  title: string
  href: string
  icon?: React.ComponentType<{ className?: string }>
}

interface FooterSection {
  label: string
  links: FooterLink[]
}

const footerLinks: FooterSection[] = [
  {
    label: "Platform",
    links: [
      { title: "Legal Analysis", href: "/legal-analysis" },
      { title: "Marketing", href: "/marketing-analysis" },
      { title: "Presentation", href: "/presentation" },
      { title: "BMC Tools", href: "/bmc" },
    ],
  },
  {
    label: "Resources",
    links: [
      { title: "SRS Generator", href: "/srs" },
      { title: "Financial Tools", href: "/financial" },
      { title: "Documentation", href: "/docs" },
      { title: "API Access", href: "/api" },
    ],
  },
  {
    label: "Company",
    links: [
      { title: "About Us", href: "/about" },
      { title: "Contact", href: "/contact" },
      { title: "Privacy Policy", href: "/privacy" },
      { title: "Terms of Service", href: "/terms" },
    ],
  },
  {
    label: "Connect",
    links: [
      { title: "Facebook", href: "#", icon: FacebookIcon },
      { title: "Instagram", href: "#", icon: InstagramIcon },
      { title: "Twitter", href: "#", icon: TwitterIcon },
      { title: "LinkedIn", href: "#", icon: LinkedinIcon },
    ],
  },
]

export function Footer() {
  return (
    <footer className="relative w-full max-w-6xl mx-auto flex flex-col items-center justify-center rounded-t-4xl border-t border-purple-500/20 bg-gradient-to-b from-purple-500/5 to-transparent px-6 py-12 lg:py-16">
      <div className="bg-purple-500/20 absolute top-0 right-1/2 left-1/2 h-px w-1/3 -translate-x-1/2 -translate-y-1/2 rounded-full blur" />

      <div className="grid w-full gap-8 xl:grid-cols-3 xl:gap-8">
        <AnimatedContainer className="space-y-4">
          <div className="flex items-center gap-3">
            <Image src="/images/logo.png" alt="ScaleUp Logo" width={48} height={48} className="size-12" />
            <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">ScaleUp</span>
          </div>
          <p className="text-white/60 text-sm max-w-xs">
            Empowering Tunisian entrepreneurs through accessible AI-driven business support.
          </p>
          <div className="text-muted-foreground mt-8 text-sm md:mt-0 md:block hidden">
            <p>&copy; {new Date().getFullYear()} ScaleUp. All rights reserved.</p>
          </div>
        </AnimatedContainer>

        <div className="mt-10 grid grid-cols-2 gap-8 md:grid-cols-4 xl:col-span-2 xl:mt-0">
          {footerLinks.map((section, index) => (
            <AnimatedContainer key={section.label} delay={0.1 + index * 0.1}>
              <div className="mb-10 md:mb-0">
                <h3 className="text-xs text-purple-300 uppercase tracking-wider">{section.label}</h3>
                <ul className="text-muted-foreground mt-4 space-y-2 text-sm">
                  {section.links.map((link) => (
                    <li key={link.title}>
                      <a
                        href={link.href}
                        className="hover:text-purple-400 inline-flex items-center transition-all duration-300"
                      >
                        {link.icon && <link.icon className="me-1 size-4" />}
                        {link.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </AnimatedContainer>
          ))}
        </div>
      </div>

      <div className="md:hidden mt-8 text-center space-y-2">
        <p className="text-muted-foreground text-sm">&copy; {new Date().getFullYear()} ScaleUp. All rights reserved.</p>
      </div>

      <div className="hidden md:block mt-8 pt-6 border-t border-purple-500/10 w-full">
        <p className="text-muted-foreground text-xs text-center">Built for Tunisian Startups</p>
      </div>
    </footer>
  )
}

type ViewAnimationProps = {
  delay?: number
  className?: ComponentProps<typeof motion.div>["className"]
  children: ReactNode
}

function AnimatedContainer({ className, delay = 0.1, children }: ViewAnimationProps) {
  const shouldReduceMotion = useReducedMotion()

  if (shouldReduceMotion) {
    return children
  }

  return (
    <motion.div
      initial={{ filter: "blur(4px)", translateY: -8, opacity: 0 }}
      whileInView={{ filter: "blur(0px)", translateY: 0, opacity: 1 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.8 }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
