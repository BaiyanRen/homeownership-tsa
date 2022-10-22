library(tidyverse)
library(modelr)
library(lubridate)
library(readxl)


if (!require(ggplot2)) install.packages('ggplot2')
library(ggplot2)
if (!require(ggpubr)) install.packages('ggpubr')
library(ggpubr)
if (!require(corrplot)) install.packages('corrplot')
library(corrplot)


rm(list=ls())
hosr <- read.csv("~/hosr_var.csv")

hosr.ts <- ts(hosr$hosr, start=1980, freq=4)
plot(hosr.ts)

time.pts = c(1:length(hosr.ts))
time.pts = c(time.pts - min(time.pts))/max(time.pts)

mav.fit = ksmooth(time.pts,hosr.ts, kernel = "box")
hosr.fit.mav = ts(mav.fit$y,start=1980,frequency=4)


##Fit a parametric quadraric polynomial

x1 = time.pts
x2 = time.pts^2
para.model = lm(hosr.ts~x1+x2)
summary(para.model)
para.fit = ts(fitted(para.model),start=1980,frequency=4)
ts.plot(hosr.ts,ylab="House Owner Rate")
lines(para.fit, lwd = 2,col = "orange")

# Residual and Residual ACF plots of the residuals from the fitted models
diff.para <- hosr.ts - para.fit
ts.plot(diff.para, xlab = "", ylab = "Residuals", main = "Parametric Quadratic Polynomial")
acf(diff.para, lag.max = 52 * 4, xlab = "", ylab = "Residuals",main = "Parametric Quadratic Polynomial")


#Difference

ts.plot(diff(hosr.ts), col = "black",main = "Differenced Home Owner Rate by Time")


x1 <- time.pts[-1]
x2 <- time.pts[-1]^2
para.model.diff<- lm(diff(hosr.ts) ~ x1 + x2)
para.fit <- ts(fitted(para.model.diff), start =1980, frequency = 4)
ts.plot(diff(hosr.ts),main = "Differenced Parametric Quadratic Polynomial Analysis")
lines(para.fit, lwd = 2,col = "orange")
