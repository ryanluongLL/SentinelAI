"use client";

import { useEffect, useRef, ReactNode } from "react";

interface AnimatedListProps{
    children: ReactNode[];
    delay?: number;
    className?: string;
}

export default function AnimatedList({
    children,
    delay = 60,
    className,
}: AnimatedListProps) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;
        const items = Array.from(container.children) as HTMLElement[];
        items.forEach((item, i) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(12px)';
            item.style.transition = `opacity 250ms ease, transform 250ms ease`;
            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateY(0';
            }, i * delay);
        });
    }, [children, delay]);

    return (
        <div ref={containerRef} className={className}>
            {children}
        </div>
    )
}