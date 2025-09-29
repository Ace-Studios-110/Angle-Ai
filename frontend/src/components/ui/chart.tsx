"use client"

import * as React from "react"
import * as RechartsPrimitive from "recharts"
import { cn } from "@/lib/utils"

// Simplified chart components that will compile without complex typing issues

export const ChartContainer = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & {
    config: Record<string, unknown>
    children: React.ComponentProps<
      typeof RechartsPrimitive.ResponsiveContainer
    >["children"]
  }
>(({ id, className, children, config, ...props }, ref) => {
  const uniqueId = React.useId()
  const chartId = `chart-${id || uniqueId.replace(/:/g, "")}`

  return (
    <div
      data-chart={chartId}
      ref={ref}
      className={cn(
        "flex aspect-video justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-none [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border [&_.recharts-sector[stroke='#fff']]:stroke-transparent [&_.recharts-sector]:outline-none [&_.recharts-surface]:outline-none",
        className
      )}
      {...props}
    >
      <ChartStyle id={chartId} config={config} />
      <RechartsPrimitive.ResponsiveContainer>
        {children}
      </RechartsPrimitive.ResponsiveContainer>
    </div>
  )
})
ChartContainer.displayName = "Chart"

const ChartStyle = ({ id, config }: { id: string; config: Record<string, unknown> }) => {
  const colorConfig = Object.entries(config).filter(
    ([, configValue]) => (configValue as { theme?: unknown }).theme
  )

  if (!colorConfig.length) {
    return null
  }

  return (
    <style
      dangerouslySetInnerHTML={{
        __html: Object.entries(config)
          .filter(([, configValue]) => (configValue as { theme?: unknown }).theme)
          .map(([key, itemConfig]) => {
            const configItem = itemConfig as { theme: string | string[] };
            const color =
              typeof configItem.theme === "string"
                ? configItem.theme
                : configItem.theme[0]

            return `
            .${id} [data-${key}] {
              color: hsl(var(--color-${color.replace(".", "-")}));
            }
            .${id} [data-${key}] .recharts-active-dot {
              background-color: hsl(var(--color-${color.replace(".", "-")}));
            }
            .${id} [data-${key}] .recharts-tooltip-cursor {
              fill: hsl(var(--color-${color.replace(".", "-")}));
            }
          `
          })
          .join("\n"),
      }}
    />
  )
}

export const ChartTooltip = RechartsPrimitive.Tooltip

export const ChartTooltipContent = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & {
    hideLabel?: boolean
    hideIndicator?: boolean
    indicator?: "line" | "dot" | "dashed" | "none"
    nameKey?: string
    label?: string
  }
>(({ className, hideLabel, hideIndicator, nameKey, label, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "grid min-w-[8rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl",
        className
      )}
      {...props}
    >
      {!hideLabel && label && (
        <div className="grid gap-1.5">
          <div className="font-medium">{label}</div>
        </div>
      )}
      <div className="grid gap-1.5">
        <div className="flex items-center gap-2">
          {!hideIndicator && (
            <div className="h-2.5 w-2.5 rounded-full bg-primary" />
          )}
          <span className="text-muted-foreground">{nameKey || "Value"}</span>
        </div>
      </div>
    </div>
  )
})
ChartTooltipContent.displayName = "ChartTooltipContent"

export const ChartLegend = RechartsPrimitive.Legend

export const ChartLegendContent = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & {
    hideIcon?: boolean
    nameKey?: string
  }
>(({ className, hideIcon, nameKey, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "flex items-center justify-center gap-4",
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-2">
        {!hideIcon && <div className="h-2.5 w-2.5 rounded-full bg-primary" />}
        <span className="text-muted-foreground">{nameKey || "Legend"}</span>
      </div>
    </div>
  )
})
ChartLegendContent.displayName = "ChartLegendContent"

// Re-export all recharts components
export const ChartBar = RechartsPrimitive.Bar
export const ChartXAxis = RechartsPrimitive.XAxis
export const ChartYAxis = RechartsPrimitive.YAxis
export const CartesianGrid = RechartsPrimitive.CartesianGrid
export const ChartLine = RechartsPrimitive.Line
export const ChartArea = RechartsPrimitive.Area
export const PieChart = RechartsPrimitive.PieChart
export const Pie = RechartsPrimitive.Pie
export const Cell = RechartsPrimitive.Cell
export const BarChart = RechartsPrimitive.BarChart
export const LineChart = RechartsPrimitive.LineChart
export const AreaChart = RechartsPrimitive.AreaChart
export const ComposedChart = RechartsPrimitive.ComposedChart
export const ScatterChart = RechartsPrimitive.ScatterChart
export const Scatter = RechartsPrimitive.Scatter
export const ResponsiveContainer = RechartsPrimitive.ResponsiveContainer