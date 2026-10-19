// Selected course handout specimen. The other three explorations were removed.
#import "styles/reference.typ": reference-layout, reference-title
#set document(title: "局部近似与误差控制 · 清爽课程讲义", author: "Recto", description: "原创数学样文；用户选定的课程讲义版式。")
#set math.equation(numbering: n => "(1." + str(n) + ")", supplement: [式])
#set heading(numbering: "1.1")
#set figure(gap: 0.65em)
#set footnote.entry(separator: line(length: 22%, stroke: 0.4pt), clearance: 1em)
#show: reference-layout

#let statement(kind, num, title, body) = block(above: 1.3em, below: 1.3em, breakable: true, inset: 0pt, stroke: none)[
  #set par(first-line-indent: 0pt)
  #block(below: 0.65em, sticky: true)[#text(weight: "bold", fill: black)[#kind #num#h(0.5em)#title]]
  #body
]
#let proof(body) = block(above: 1.1em, below: 1.3em, breakable: true)[
  #set par(first-line-indent: 0pt)
  #text(weight: "bold")[证明]#h(0.7em)#body#h(1fr)$square$
]
#let note(title, body) = block(above: 0.85em, below: 0.85em)[
  #set par(first-line-indent: 0pt)
  #text(size: 12pt, fill: black, weight: "bold")[#title]#h(0.7em)#text(size: 12pt)[#body]
]
#counter(heading).update(1)
#reference-title([局部近似与误差控制], [Local Approximation and Error Control])

微积分的一种基本方法，是用容易计算的对象近似复杂对象。直线刻画函数在一点附近的主要变化，二次项补充弯曲信息，而余项说明这种替代在多大范围内可信。本章从可微性出发，建立 Taylor 近似，并用误差估计连接符号推导与实际计算。

这三个层次应当分别理解：*近似式*给出可计算的表达式，*误差界*给出可靠程度，*适用范围*说明结论成立的条件。它们共同构成局部分析（local analysis）的基本语言。

== 从变化率到局部模型

设函数 $f$ 在点 $a$ 的邻域内有定义。当自变量的增量 $h$ 趋于零时，我们希望用一个关于 $h$ 的简单表达式描述 $f(a+h)-f(a)$。最自然的候选是一次函数。

#statement("定义", "1.1", [可微性], [
  若存在实数 $L$，使得
  $ f(a+h) = f(a) + L h + o(h), quad h -> 0, $ <differentiability>
  则称 $f$ 在 $a$ 处可微，并记 $f'(a)=L$。这里 $o(h)$ 表示满足 $o(h)/h -> 0$ 的余项。
])

线性近似只保留一阶变化。当误差本身也是研究对象时，我们需要更精细的表达。若二阶导数存在，就可以进一步考察二次项 $f''(a)h^2/2$。#footnote[本文在一元情形中使用增量 $h$；多元情形使用向量 $bold(h)$。记号 $o$ 与 $O$ 分别表示高阶无穷小和同阶有界估计。]

#note([阅读线索], [先辨认每个近似式的展开点，再查看余项的阶数。函数具有多少阶导数，与能够控制多小的误差密切相关。])

== Taylor 公式与余项

为了得到可用的误差界，仅知道“余项趋于零”是不够的。下面给出二阶 Taylor 公式的积分余项形式。积分表达保留了三阶导数的信息，因此可以直接导出定量估计。

#statement("定理", "1.2", [二阶 Taylor 公式], [
  设 $f$ 在包含 $a$ 与 $a+h$ 的区间上具有连续的三阶导数，则
  $ f(a+h) = f(a)+f'(a)h+1/2 f''(a)h^2+R_2(h), $ <taylor>
  其中
  $ R_2(h)=1/2 integral_0^h (h-t)^2 f'''(a+t) dif t. $ <remainder>
  若在该区间上 $abs(f'''(x)) <= M$，则 $abs(R_2(h)) <= M abs(h)^3/6$。
])

#proof([
  令 $g(t)=f(a+t)$，对 @remainder 中的积分连续使用两次分部积分。记 $I=R_2(h)$，则
  $ I &= -1/2 h^2 g''(0) + integral_0^h (h-t)g''(t) dif t \
      &= -1/2 h^2 g''(0) - h g'(0) + integral_0^h g'(t) dif t \
      &= g(h)-g(0)-h g'(0)-1/2 h^2 g''(0). $
  移项即得 @taylor。当 $h >= 0$ 时，对积分取绝对值可得 $abs(I) <= M h^3/6$；当 $h<0$ 时交换积分上下限，同样得到 $M abs(h)^3/6$。
])

从证明可以看出，Taylor 多项式与原函数在展开点具有相同的函数值、一阶导数和二阶导数。余项则记录两者在离开展开点之后的差异。精度取决于步长和高阶导数，不能只凭多项式次数判断。

#statement("例", "1.3", [指数函数的二阶近似], [
  取 $f(x)=e^x$，在 $a=0$ 处展开，得到 $e^h=1+h+h^2/2+R_2(h)$。对 $abs(h)<=0.1$，可取 $M=e^(0.1)$，所以
  $ abs(R_2(h)) <= e^(0.1)/6 abs(h)^3 < 1.85 times 10^(-4). $
])

#note([条件与结论], [连续三阶导数是本定理使用的充分条件。不要把这一条件误读成任何二阶近似都必须满足的必要条件。])

== 误差的尺度与可视化

考虑 $sin x$ 在原点附近的三次近似 $p_3(x)=x-x^3/6$。由于四阶项在原点处为零，对四阶 Taylor 公式使用五阶余项估计，可得

$ abs(sin x - p_3(x)) <= abs(x)^5/120. $ <sine-bound>

图 1 展示两个函数在 $[-1.5,1.5]$ 上的形状。原点附近的曲线几乎重合；离开原点后，三次项仍有修正作用，但误差逐渐可见。图形帮助建立直觉，严格的精度保证仍来自 @sine-bound。

#figure(
  image("assets/approximation.svg", width: 82%),
  caption: [正弦函数与三次近似。原点附近吻合较好，向区间两端逐渐分离。],
)

下表同时列出实际绝对误差与理论上界。上界不必等于实际误差，但必须在给定条件下始终有效。减小 $x$ 的绝对值，比单纯保留更多小数位更能改变近似的可靠程度。

#figure(
  table(
    columns: (1fr, 1.6fr, 1.7fr), inset: (x: 5pt, y: 7pt), align: (center, right, right),
    stroke: (top: none, bottom: 0.35pt, left: none, right: none),
    table.hline(stroke: 0.6pt),
    table.header([$x$], [实际绝对误差], [理论上界 $abs(x)^5/120$]),
    table.hline(stroke: 0.35pt),
    [0.25], [$8.126 times 10^(-6)$], [$8.138 times 10^(-6)$],
    [0.50], [$2.589 times 10^(-4)$], [$2.604 times 10^(-4)$],
    [1.00], [$8.138 times 10^(-3)$], [$8.333 times 10^(-3)$],
    table.hline(stroke: 0.6pt),
  ),
  caption: [实际误差与理论上界；实际误差以科学记数法四舍五入。],
)

#note([数值判断], [若要求绝对误差不超过 $10^(-4)$，充分条件是 $abs(x) <= (120 times 10^(-4))^(1/5)$。这是从误差要求反推步长范围的基本方法。])

== 多元情形与二次型

一元近似中的导数，在多元情形中分别对应梯度（gradient）与 Hessian 矩阵。设 #box[$f: RR^n -> RR$] 在 $bold(a)$ 的邻域内三阶连续可微，则

$ f(bold(a)+bold(h)) &= f(bold(a)) + nabla f(bold(a))^T bold(h) \
  &quad + 1/2 bold(h)^T H_f (bold(a)) bold(h) + O(norm(bold(h))^3). $ <multivariable>

这里的二次型汇集了纯二阶偏导数与混合偏导数的信息。它不仅描述沿坐标轴的弯曲，也描述不同方向之间的耦合；矩阵写法使这种结构一目了然。

#statement("例", "1.4", [一个具有不同曲率方向的模型], [
  令 $f(x,y)=e^x cos y$。在原点处，
  $ nabla f(0,0)=mat(1; 0), quad H_f (0,0)=mat(1,0;0,-1). $
  因而 $f(x,y)=1+x+(x^2-y^2)/2+O((x^2+y^2)^(3/2))$。二次项在 $x$ 方向为正、在 $y$ 方向为负，反映了两种相反的局部弯曲趋势。
])

== 练习与进一步思考

#set enum(numbering: "1.", indent: 0pt, body-indent: 1.5em, spacing: 0.7em)
+ 将 $ln(1+x)$ 在原点处展开到二阶，并在 $abs(x)<=1/2$ 上给出一个明确的三阶误差界。
+ 利用 @sine-bound，求一个使 $abs(sin x-p_3(x))<=10^(-5)$ 成立的充分条件。比较所得范围与图中的直觉判断。
+ 计算 $f(x,y)=e^(x+y)$ 在原点处的二阶 Taylor 多项式，解释混合项 $x y$ 的来源。

#block(above: 1.1em, below: 0.8em)[
  #set par(first-line-indent: 0pt)
  #text(font: "Times New Roman", size: 12pt, weight: "bold")[A local model is a controlled simplification.]
  #v(0.45em)
  #text(lang: "en", size: 12pt)[A Taylor polynomial captures the behaviour of a smooth function near a chosen point. The remainder determines how far the approximation can be trusted. Always read an approximation together with its assumptions and its error bound.]
]

#note([本章要点], [展开点决定局部模型，导数决定多项式系数，余项决定精度。处理多元函数时，先辨认梯度与 Hessian，再讨论方向上的变化。])
