// Vitest mock for motion/react (Framer Motion v12)
// Returns passthrough React components so tests can render without animation engine
import React from 'react'

const createMotionComponent = (tag: string) => {
  const component = React.forwardRef<HTMLElement, React.HTMLAttributes<HTMLElement> & Record<string, unknown>>(
    ({ children, ...props }, ref) => {
      const filtered = Object.fromEntries(
        Object.entries(props).filter(([k]) =>
          !['initial', 'animate', 'exit', 'transition', 'whileHover', 'whileTap', 'whileFocus', 'variants', 'layout', 'layoutId'].includes(k)
        )
      )
      return React.createElement(tag, { ...filtered, ref }, children)
    }
  )
  component.displayName = `motion.${tag}`
  return component
}

export const motion = new Proxy({} as Record<string, ReturnType<typeof createMotionComponent>>, {
  get: (_target, prop: string) => createMotionComponent(prop),
})

export const AnimatePresence = ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children)

export const useAnimation = () => ({ start: () => {}, stop: () => {}, set: () => {} })
export const useMotionValue = (initial: number) => ({ get: () => initial, set: () => {} })
export const useTransform = (_val: unknown, _from: unknown, _to: unknown) => ({ get: () => 0 })
export const useSpring = (val: number) => ({ get: () => val })
export const useScroll = () => ({ scrollY: { get: () => 0 }, scrollYProgress: { get: () => 0 } })
