"use client"
"use client"

import { useState, useEffect, useRef } from "react"
import { Menu, X, ArrowRight, LogIn, LogOut, UserCircle2 } from "lucide-react"
import Image from "next/image"
import Link from "next/link"
import { fetchCurrentUser, logoutCurrentUser } from "@/lib/auth-client"

const navigation = [
  { name: "Legal Analysis", href: "/legal-analysis" },
  { name: "Marketing", href: "/marketing-analysis" },
  { name: "Presentation", href: "/presentation" },
  { name: "BMC", href: "/bmc" },
  { name: "SRS", href: "/srs" },
  { name: "Financial", href: "/financial-advisor" },
]

export function GlassmorphismNav() {
  const [isOpen, setIsOpen] = useState(false)
  const [isVisible, setIsVisible] = useState(true)
  const [hasLoaded, setHasLoaded] = useState(false)
  const [currentUser, setCurrentUser] = useState<{ firstName: string; lastName: string; email: string; plan: string } | null>(null)
  const [isSigningOut, setIsSigningOut] = useState(false)
  const lastScrollY = useRef(0)

  useEffect(() => {
    const timer = setTimeout(() => {
      setHasLoaded(true)
    }, 100)

    const controlNavbar = () => {
      if (typeof window !== "undefined") {
        const currentScrollY = window.scrollY

        // Only hide/show after scrolling past 50px to avoid flickering at top
        if (currentScrollY > 50) {
          if (currentScrollY > lastScrollY.current && currentScrollY - lastScrollY.current > 5) {
            // Scrolling down - hide navbar
            setIsVisible(false)
          } else if (lastScrollY.current - currentScrollY > 5) {
            // Scrolling up - show navbar
            setIsVisible(true)
          }
        } else {
          // Always show navbar when near top
          setIsVisible(true)
        }

        lastScrollY.current = currentScrollY
      }
    }

    if (typeof window !== "undefined") {
      window.addEventListener("scroll", controlNavbar, { passive: true })

      void fetchCurrentUser().then((payload) => {
        if (payload?.user) {
          setCurrentUser(payload.user)
        }
      })

      return () => {
        window.removeEventListener("scroll", controlNavbar)
        clearTimeout(timer)
      }
    }

    return () => clearTimeout(timer)
  }, []) // Removed lastScrollY dependency to prevent infinite re-renders

  // Theme toggle state (simple, toggles 'dark' class on <html>)
  const [isDark, setIsDark] = useState<boolean>(false)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const hasDark = document.documentElement.classList.contains("dark")
      setIsDark(hasDark)
    }
  }, [])
  const toggleTheme = () => {
    if (typeof window === "undefined") return
    const el = document.documentElement
    if (el.classList.contains("dark")) {
      el.classList.remove("dark")
      setIsDark(false)
    } else {
      el.classList.add("dark")
      setIsDark(true)
    }
  }

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const scrollToSection = (href: string) => {
    if (href.startsWith("/")) {
      return
    }

    const element = document.querySelector(href)
    if (element) {
      const rect = element.getBoundingClientRect()
      const currentScrollY = window.pageYOffset || document.documentElement.scrollTop
      const elementAbsoluteTop = rect.top + currentScrollY
      const navbarHeight = 100
      const targetPosition = Math.max(0, elementAbsoluteTop - navbarHeight)

      window.scrollTo({
        top: targetPosition,
        behavior: "smooth",
      })
    }
    setIsOpen(false)
  }

  const handleLogout = async () => {
    setIsSigningOut(true)
    try {
      await logoutCurrentUser()
      setCurrentUser(null)
      window.location.href = "/"
    } finally {
      setIsSigningOut(false)
    }
  }

  const authCta = currentUser ? (
    <div className="flex items-center gap-3">
      <Link
        href="/presentation"
        className="hidden md:inline-flex items-center gap-2 rounded-full bg-white px-5 py-2 text-sm font-medium text-black transition hover:scale-105 hover:bg-gray-50"
      >
        <UserCircle2 size={16} />
        {currentUser.firstName}
      </Link>
      <button
        type="button"
        onClick={handleLogout}
        disabled={isSigningOut}
        className="hidden md:inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-5 py-2 text-sm font-medium text-white transition hover:bg-white/15 disabled:opacity-60"
      >
        <LogOut size={16} />
        {isSigningOut ? "Signing out" : "Logout"}
      </button>
    </div>
  ) : (
    <Link
      href="/auth"
      className="hidden md:inline-flex items-center gap-2 rounded-full bg-white px-5 py-2 text-sm font-medium text-black transition hover:scale-105 hover:bg-gray-50"
    >
      <LogIn size={16} />
      Sign in
    </Link>
  )

  return (
    <>
      <nav
        className={`fixed top-4 md:top-8 left-1/2 -translate-x-1/2 z-50 transition-all duration-500 ${
          isVisible ? "translate-y-0 opacity-100" : "-translate-y-20 md:-translate-y-24 opacity-0"
        } ${hasLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
        style={{
          transition: hasLoaded ? "all 0.5s ease-out" : "opacity 0.8s ease-out, transform 0.8s ease-out",
        }}
      >
        {/* Main Navigation */}
        <div className="w-[90vw] max-w-xs md:max-w-4xl mx-auto">
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-full px-4 py-3 md:px-6 md:py-2">
            <div className="flex items-center justify-between">
              {/* Logo */}
              <Link
                href="/"
                className="flex items-center hover:scale-105 transition-transform duration-200 cursor-pointer"
              >
                <div className="w-10 h-10 md:w-12 md:h-12 flex items-center justify-center">
                  <Image
                    src="/images/scaleup-logo.jpg"
                    alt="ScaleUp"
                    width={40}
                    height={40}
                    className="w-full h-full object-contain"
                  />
                </div>
              </Link>


              {/* Desktop Navigation */}
              <div className="hidden md:flex items-center space-x-6">
                {navigation.map((item) =>
                  item.href.startsWith("/") ? (
                    <Link
                      key={item.name}
                      href={item.href}
                      className="text-foreground hover:opacity-90 hover:scale-105 transition-all duration-200 font-medium cursor-pointer"
                    >
                      {item.name}
                    </Link>
                  ) : (
                    <button
                      key={item.name}
                      onClick={() => scrollToSection(item.href)}
                      className="text-foreground hover:opacity-90 hover:scale-105 transition-all duration-200 font-medium cursor-pointer"
                    >
                      {item.name}
                    </button>
                  ),
                )}
                {/* Theme toggle (desktop) */}
                <button
                  type="button"
                  onClick={toggleTheme}
                  aria-label="Toggle dark mode"
                  className="ml-2 inline-flex items-center justify-center rounded-full p-2 bg-white/10 text-foreground hover:bg-white/15"
                >
                  {isDark ? (
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-sun"><circle cx="12" cy="12" r="5"></circle><path d="M12 1v2"></path><path d="M12 21v2"></path><path d="M4.22 4.22l1.42 1.42"></path><path d="M18.36 18.36l1.42 1.42"></path><path d="M1 12h2"></path><path d="M21 12h2"></path><path d="M4.22 19.78l1.42-1.42"></path><path d="M18.36 5.64l1.42-1.42"></path></svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-moon"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"></path></svg>
                  )}
                </button>

              </div>

              {/* Desktop CTA Button */}
              <div className="hidden md:block">{authCta}</div>

              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="md:hidden text-white hover:scale-110 transition-transform duration-200 cursor-pointer"
              >
                <div className="relative w-6 h-6">
                  <Menu
                    size={24}
                    className={`absolute inset-0 transition-all duration-300 ${
                      isOpen ? "opacity-0 rotate-180 scale-75" : "opacity-100 rotate-0 scale-100"
                    }`}
                  />
                  <X
                    size={24}
                    className={`absolute inset-0 transition-all duration-300 ${
                      isOpen ? "opacity-100 rotate-0 scale-100" : "opacity-0 -rotate-180 scale-75"
                    }`}
                  />
                </div>
              </button>
            </div>
          </div>
        </div>

        <div className="md:hidden relative">
          {/* Backdrop overlay */}
          <div
            className={`fixed inset-0 bg-black/20 backdrop-blur-sm transition-all duration-300 ${
              isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
            }`}
            onClick={() => setIsOpen(false)}
            style={{ top: "0", left: "0", right: "0", bottom: "0", zIndex: -1 }}
          />

          {/* Menu container */}
          <div
            className={`mt-2 w-[90vw] max-w-xs mx-auto transition-all duration-500 ease-out transform-gpu ${
              isOpen ? "opacity-100 translate-y-0 scale-100" : "opacity-0 -translate-y-8 scale-95 pointer-events-none"
            }`}
          >
            <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4 shadow-2xl">
              <div className="flex flex-col space-y-1">
                <div className="flex justify-end mb-2">
                  <button
                    type="button"
                    onClick={toggleTheme}
                    aria-label="Toggle dark mode"
                    className="inline-flex items-center justify-center rounded-full p-2 bg-white/10 text-foreground hover:bg-white/15"
                  >
                    {isDark ? (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-sun"><circle cx="12" cy="12" r="5"></circle><path d="M12 1v2"></path><path d="M12 21v2"></path><path d="M4.22 4.22l1.42 1.42"></path><path d="M18.36 18.36l1.42 1.42"></path><path d="M1 12h2"></path><path d="M21 12h2"></path><path d="M4.22 19.78l1.42-1.42"></path><path d="M18.36 5.64l1.42-1.42"></path></svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-moon"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"></path></svg>
                    )}
                  </button>
                </div>
                {navigation.map((item, index) =>
                  item.href.startsWith("/") ? (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={`text-white/80 hover:text-white hover:bg-white/10 rounded-lg px-3 py-3 text-left transition-all duration-300 font-medium cursor-pointer transform hover:scale-[1.02] hover:translate-x-1 ${
                        isOpen ? "animate-mobile-menu-item" : ""
                      }`}
                      style={{
                        animationDelay: isOpen ? `${index * 80 + 100}ms` : "0ms",
                      }}
                      onClick={() => setIsOpen(false)}
                    >
                      {item.name}
                    </Link>
                  ) : (
                    <button
                      key={item.name}
                      onClick={() => scrollToSection(item.href)}
                      className={`text-white/80 hover:text-white hover:bg-white/10 rounded-lg px-3 py-3 text-left transition-all duration-300 font-medium cursor-pointer transform hover:scale-[1.02] hover:translate-x-1 ${
                        isOpen ? "animate-mobile-menu-item" : ""
                      }`}
                      style={{
                        animationDelay: isOpen ? `${index * 80 + 100}ms` : "0ms",
                      }}
                    >
                      {item.name}
                    </button>
                  ),
                )}
                <div className="h-px bg-white/10 my-2" />
                {currentUser ? (
                  <>
                    <Link
                      href="/presentation"
                      className={`bg-white hover:bg-gray-50 text-black font-medium px-6 py-3 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105 hover:shadow-lg cursor-pointer group transform ${
                        isOpen ? "animate-mobile-menu-item" : ""
                      }`}
                      style={{
                        animationDelay: isOpen ? `${navigation.length * 80 + 150}ms` : "0ms",
                      }}
                      onClick={() => setIsOpen(false)}
                    >
                      <span className="mr-2">Open platform</span>
                      <ArrowRight size={16} className="transition-transform duration-300 group-hover:translate-x-1" />
                    </Link>
                    <button
                      type="button"
                      onClick={handleLogout}
                      disabled={isSigningOut}
                      className={`border border-white/15 bg-white/10 text-white font-medium px-6 py-3 rounded-full flex items-center justify-center transition-all duration-300 hover:bg-white/15 disabled:opacity-60 ${
                        isOpen ? "animate-mobile-menu-item" : ""
                      }`}
                      style={{
                        animationDelay: isOpen ? `${navigation.length * 80 + 220}ms` : "0ms",
                      }}
                    >
                      <LogOut size={16} className="mr-2" />
                      {isSigningOut ? "Signing out" : "Logout"}
                    </button>
                  </>
                ) : (
                  <Link
                    href="/auth"
                    className={`bg-white hover:bg-gray-50 text-black font-medium px-6 py-3 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105 hover:shadow-lg cursor-pointer group transform ${
                      isOpen ? "animate-mobile-menu-item" : ""
                    }`}
                    style={{
                      animationDelay: isOpen ? `${navigation.length * 80 + 150}ms` : "0ms",
                    }}
                    onClick={() => setIsOpen(false)}
                  >
                    <span className="mr-2">Sign in</span>
                    <LogIn size={16} className="transition-transform duration-300 group-hover:translate-x-1" />
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>
    </>
  )
}

