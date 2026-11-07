import React from "react";
import { Link as RouterLink } from "react-router-dom";

export interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  children?: React.ReactNode;
}

export const Link = React.forwardRef<HTMLAnchorElement, LinkProps>(
  ({ href, children, ...props }, ref) => {
    if (href.startsWith("http") || href.startsWith("#") || href.startsWith("mailto:")) {
      return (
        <a ref={ref} href={href} {...props}>
          {children}
        </a>
      );
    }
    return (
      <RouterLink ref={ref} to={href} {...(props as any)}>
        {children}
      </RouterLink>
    );
  }
);

Link.displayName = "NextLinkShim";

export default Link;

export interface ImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  width?: number | string;
  height?: number | string;
}

export const Image = React.forwardRef<HTMLImageElement, ImageProps>(
  ({ width, height, alt = "", ...props }, ref) => {
    return <img ref={ref} width={width} height={height} alt={alt} {...props} />;
  }
);

Image.displayName = "NextImageShim";
