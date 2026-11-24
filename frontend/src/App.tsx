import { AnimatePresence, motion } from "motion/react"
import { useState } from "react"
import { Choose } from "@/screens/Choose"
import { Splash } from "@/screens/Splash"
import { AnalysisSystem } from "@/systems/analysis/AnalysisSystem"
import { TerraSystem } from "@/systems/terra/TerraSystem"

export type Screen = "splash" | "choose" | "analysis" | "terra"

export default function App() {
  const [screen, setScreen] = useState<Screen>("splash")

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={screen}
        className="min-h-svh"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.25 }}
      >
        {screen === "splash" && <Splash onStart={() => setScreen("choose")} />}
        {screen === "choose" && <Choose onPick={setScreen} />}
        {screen === "analysis" && <AnalysisSystem onNavigate={setScreen} />}
        {screen === "terra" && <TerraSystem onNavigate={setScreen} />}
      </motion.div>
    </AnimatePresence>
  )
}
