import { Button } from "@/components/ui/button"
import RotatingText from "./RotatingText"

const ArrowRight = () => (
  <svg
    className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
)

const Play = () => (
  <svg
    className="mr-2 h-5 w-5 group-hover:scale-110 transition-transform"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
    />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

export function HeroSection() {
  return (
    <section className="min-h-screen flex items-center justify-center px-4 py-20 relative">
      <div className="max-w-4xl mx-auto text-center relative z-10 animate-fade-in-hero">
        {/* Badge */}
        <div className="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-white text-sm font-medium mb-8 mt-12 animate-fade-in-badge">
          <span className="w-2 h-2 bg-purple-400 rounded-full mr-2 animate-pulse"></span>
          AI-Powered Startup Platform
        </div>

        {/* Main Heading */}
        <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-7xl font-bold text-balance mb-6 animate-fade-in-heading">
          <span className="text-foreground">Empower Your</span>
          <br />
          <span className="inline-flex items-center justify-center flex-wrap gap-2 mt-4 sm:mt-6 md:mt-8">
            <span className="bg-gradient-to-r from-purple-400 via-violet-400 to-indigo-400 bg-clip-text text-transparent">Startup</span>
            <RotatingText
              texts={["Growth", "Validation", "Innovation", "Success", "Launch"]}
              mainClassName="px-2 sm:px-2 md:px-3 bg-gradient-to-r from-purple-500 to-indigo-600 text-white overflow-hidden py-1 sm:py-1 md:py-2 justify-center rounded-lg shadow-lg"
              staggerFrom={"last"}
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "-120%" }}
              staggerDuration={0.025}
              splitLevelClassName="overflow-hidden pb-1 sm:pb-1 md:pb-1"
              transition={{ type: "spring", damping: 30, stiffness: 400 }}
              rotationInterval={2000}
            />
          </span>
        </h1>

        {/* Subheading */}
        <p className="text-base sm:text-xl md:text-2xl text-white/90 text-balance max-w-sm sm:max-w-3xl mx-auto mb-8 sm:mb-12 leading-relaxed px-4 sm:px-0 animate-fade-in-subheading font-light">
          ScaleUp helps Tunisian startups launch, validate, and grow their businesses using artificial intelligence. 
          From business model validation to legal assistance and intelligent consulting.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8 sm:mb-16 animate-fade-in-buttons">
          <Button
            size="lg"
            className="bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white rounded-full px-8 py-4 text-lg font-medium transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-purple-500/25 group cursor-pointer relative overflow-hidden"
          >
            Get Started
            <ArrowRight />
          </Button>

          <Button
            variant="outline"
            size="lg"
            className="rounded-full px-8 py-4 text-lg font-medium border-purple-400/50 hover:bg-purple-500/10 transition-all duration-200 hover:scale-105 group bg-transparent cursor-pointer text-white"
          >
            <Play />
            Try Demo
          </Button>
        </div>

        {/* Trust Indicators */}
        <div className="text-center px-4 hidden sm:block overflow-hidden animate-fade-in-trust">
          <p className="text-sm text-white/70 mb-6">Trusted by innovative Tunisian startups</p>
          <div className="relative overflow-hidden w-full max-w-4xl mx-auto">
            <div className="flex items-center gap-8 opacity-60 hover:opacity-80 transition-all duration-500 animate-slide-left">
              <div className="flex items-center gap-8 whitespace-nowrap">
                <div className="text-base sm:text-lg font-semibold text-purple-300">TunisTech</div>
                <div className="text-base sm:text-lg font-semibold text-indigo-300">InnovateTN</div>
                <div className="text-base sm:text-lg font-semibold text-violet-300">StartupCarthage</div>
                <div className="text-base sm:text-lg font-semibold text-purple-300">MedTechTN</div>
                <div className="text-base sm:text-lg font-semibold text-indigo-300">AgriTech Tunisia</div>
                <div className="text-base sm:text-lg font-semibold text-violet-300">FinTech Sousse</div>
              </div>
              {/* Duplicate for seamless loop */}
              <div className="flex items-center gap-8 whitespace-nowrap">
                <div className="text-base sm:text-lg font-semibold text-purple-300">TunisTech</div>
                <div className="text-base sm:text-lg font-semibold text-indigo-300">InnovateTN</div>
                <div className="text-base sm:text-lg font-semibold text-violet-300">StartupCarthage</div>
                <div className="text-base sm:text-lg font-semibold text-purple-300">MedTechTN</div>
                <div className="text-base sm:text-lg font-semibold text-indigo-300">AgriTech Tunisia</div>
                <div className="text-base sm:text-lg font-semibold text-violet-300">FinTech Sousse</div>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Trust Indicators */}
        <div className="text-center px-4 mb-8 sm:hidden overflow-hidden animate-fade-in-trust">
          <p className="text-sm text-white/70 mb-6">Trusted by innovative Tunisian startups</p>
          <div className="relative overflow-hidden w-full max-w-sm mx-auto">
            <div className="absolute left-0 top-0 w-8 h-full bg-gradient-to-r from-background to-transparent z-10 pointer-events-none"></div>
            <div className="absolute right-0 top-0 w-8 h-full bg-gradient-to-l from-background to-transparent z-10 pointer-events-none"></div>
            <div className="flex items-center gap-6 opacity-60 animate-slide-left-mobile">
              <div className="flex items-center gap-6 whitespace-nowrap">
                <div className="text-sm font-semibold text-purple-300">TunisTech</div>
                <div className="text-sm font-semibold text-indigo-300">InnovateTN</div>
                <div className="text-sm font-semibold text-violet-300">StartupCarthage</div>
                <div className="text-sm font-semibold text-purple-300">MedTechTN</div>
                <div className="text-sm font-semibold text-indigo-300">AgriTech Tunisia</div>
                <div className="text-sm font-semibold text-violet-300">FinTech Sousse</div>
              </div>
              <div className="flex items-center gap-6 whitespace-nowrap">
                <div className="text-sm font-semibold text-purple-300">TunisTech</div>
                <div className="text-sm font-semibold text-indigo-300">InnovateTN</div>
                <div className="text-sm font-semibold text-violet-300">StartupCarthage</div>
                <div className="text-sm font-semibold text-purple-300">MedTechTN</div>
                <div className="text-sm font-semibold text-indigo-300">AgriTech Tunisia</div>
                <div className="text-sm font-semibold text-violet-300">FinTech Sousse</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
