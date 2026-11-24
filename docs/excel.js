/* Excel practice. Shortcuts are for Windows Excel. Keep ids stable. */
window.EXCEL_SHORTCUTS = [
  {id:"x1", q:"Toggle a cell reference between relative and absolute ($A$1, A$1, $A1, A1)", a:"F4", o:["F4","F2","Ctrl+$","F9"]},
  {id:"x2", q:"Edit the active cell without retyping it", a:"F2", o:["F2","F4","Ctrl+E","Enter"]},
  {id:"x3", q:"Copy the formula from the cell above into the selected cells", a:"Ctrl+D", o:["Ctrl+D","Ctrl+R","Ctrl+C","Ctrl+Shift+D"]},
  {id:"x4", q:"Copy the formula from the left across a selected row", a:"Ctrl+R", o:["Ctrl+R","Ctrl+D","Ctrl+L","Alt+R"]},
  {id:"x5", q:"Open the Format Cells dialog", a:"Ctrl+1", o:["Ctrl+1","Ctrl+F","Alt+F","Ctrl+Shift+F"]},
  {id:"x6", q:"Paste values only", a:"Alt, E, S, V (or Ctrl+Alt+V then V)", o:["Alt, E, S, V (or Ctrl+Alt+V then V)","Ctrl+Shift+V","Alt, H, V, F","Ctrl+V twice"]},
  {id:"x7", q:"Jump to the edge of the data region (e.g., last filled cell down)", a:"Ctrl+Arrow", o:["Ctrl+Arrow","Shift+Arrow","Alt+Arrow","End then Home"]},
  {id:"x8", q:"Select from the current cell to the edge of the data", a:"Ctrl+Shift+Arrow", o:["Ctrl+Shift+Arrow","Shift+Arrow","Ctrl+A","Alt+Shift+Arrow"]},
  {id:"x9", q:"Select the entire row", a:"Shift+Space", o:["Shift+Space","Ctrl+Space","Ctrl+Shift+R","Alt+Space"]},
  {id:"x10", q:"Select the entire column", a:"Ctrl+Space", o:["Ctrl+Space","Shift+Space","Ctrl+Shift+C","Alt+C"]},
  {id:"x11", q:"Insert rows/columns (after selecting a row or column)", a:"Ctrl+Shift+Plus (Ctrl++)", o:["Ctrl+Shift+Plus (Ctrl++)","Ctrl+I","Alt+I","Ctrl+Enter"]},
  {id:"x12", q:"Delete the selected rows/columns", a:"Ctrl+Minus (Ctrl+-)", o:["Ctrl+Minus (Ctrl+-)","Delete","Ctrl+X","Alt+D"]},
  {id:"x13", q:"Show formulas instead of values across the sheet", a:"Ctrl+` (grave accent)", o:["Ctrl+` (grave accent)","Ctrl+F","F9","Ctrl+Shift+F"]},
  {id:"x14", q:"Jump to the cells a formula refers to (precedents)", a:"Ctrl+[", o:["Ctrl+[","Ctrl+]","Ctrl+P","F5"]},
  {id:"x15", q:"Trace precedents with arrows", a:"Alt, M, P", o:["Alt, M, P","Alt, M, D","Alt, T, P","Ctrl+T"]},
  {id:"x16", q:"Remove trace arrows", a:"Alt, M, A, A", o:["Alt, M, A, A","Alt, M, P","Esc","Ctrl+Z"]},
  {id:"x17", q:"AutoSum the cells above", a:"Alt+=", o:["Alt+=","Ctrl+=","Ctrl+S","Shift+="]},
  {id:"x18", q:"Move to the next worksheet", a:"Ctrl+Page Down", o:["Ctrl+Page Down","Ctrl+Tab","Alt+Right","Ctrl+Right"]},
  {id:"x19", q:"Autofit the selected column width", a:"Alt, H, O, I", o:["Alt, H, O, I","Alt, H, O, A","Ctrl+W","Alt, W, F"]},
  {id:"x20", q:"Freeze panes at the selected cell", a:"Alt, W, F, F", o:["Alt, W, F, F","Alt, H, F, F","Ctrl+Shift+F","Alt, V, F"]},
  {id:"x21", q:"Increase decimal places", a:"Alt, H, 0", o:["Alt, H, 0","Alt, H, 9","Ctrl+.","Ctrl+Shift+1"]},
  {id:"x22", q:"Apply number format with commas and 2 decimals", a:"Ctrl+Shift+1 (Ctrl+!)", o:["Ctrl+Shift+1 (Ctrl+!)","Ctrl+Shift+4 ($)","Ctrl+Shift+5 (%)","Ctrl+1"]},
  {id:"x23", q:"Apply percent format", a:"Ctrl+Shift+5 (Ctrl+%)", o:["Ctrl+Shift+5 (Ctrl+%)","Ctrl+Shift+1","Alt, H, P","Ctrl+5"]},
  {id:"x24", q:"Recalculate all formulas (when calculation is manual)", a:"F9", o:["F9","F4","F2","Ctrl+R"]},
  {id:"x25", q:"Enter the same entry in every selected cell", a:"Ctrl+Enter", o:["Ctrl+Enter","Alt+Enter","Shift+Enter","Ctrl+D"]},
  {id:"x26", q:"Start a new line inside a cell", a:"Alt+Enter", o:["Alt+Enter","Ctrl+Enter","Shift+Enter","Tab"]},
  {id:"x27", q:"Group selected rows (outline)", a:"Alt+Shift+Right Arrow", o:["Alt+Shift+Right Arrow","Ctrl+G","Alt+Shift+Left Arrow","Ctrl+Shift+G"]},
  {id:"x28", q:"Open Go To (and Go To Special)", a:"F5 / Ctrl+G", o:["F5 / Ctrl+G","F3","Ctrl+F","F6"]}
];

window.EXCEL_FUNCTIONS = [
  {id:"f1", q:"Look up a value in one column and return the value in another column on the same row, without breaking when columns are inserted", a:"INDEX/MATCH (or XLOOKUP)", o:["INDEX/MATCH (or XLOOKUP)","VLOOKUP with a hard-coded column number","SUMPRODUCT","OFFSET"]},
  {id:"f2", q:"Add up revenue only for rows where Region = \"Texas\" and Year = 2026", a:"SUMIFS", o:["SUMIFS","SUMIF","COUNTIFS","SUMPRODUCT only"]},
  {id:"f3", q:"Discount cash flows that arrive on specific, uneven dates", a:"XNPV", o:["XNPV","NPV","PV","IRR"]},
  {id:"f4", q:"Return of an investment with cash flows on specific dates", a:"XIRR", o:["XIRR","IRR","RATE","MIRR"]},
  {id:"f5", q:"Show 0 instead of #DIV/0! when a margin's denominator is empty", a:"IFERROR", o:["IFERROR","ISBLANK","IFS","N/A"]},
  {id:"f6", q:"Get the last day of the month 3 months after a date (for quarter-end columns)", a:"EOMONTH", o:["EOMONTH","EDATE","DATEDIF","WORKDAY"]},
  {id:"f7", q:"Multiply two ranges element by element and add the results (e.g., weighted average)", a:"SUMPRODUCT", o:["SUMPRODUCT","MMULT","PRODUCT","SUMIFS"]},
  {id:"f8", q:"Annual growth rate from $80 to $100 over 3 years, in one formula", a:"=(100/80)^(1/3)-1", o:["=(100/80)^(1/3)-1","=(100-80)/80/3","=100/80/3","=GROWTH(100,80,3)"]},
  {id:"f9", q:"Build a two-way sensitivity table of share price vs. WACC and growth", a:"Data Table (What-If Analysis)", o:["Data Table (What-If Analysis)","Goal Seek","Scenario Manager","PivotTable"]},
  {id:"f10", q:"Find the purchase price that makes IRR exactly 20%", a:"Goal Seek", o:["Goal Seek","Data Table","Solver is required","XIRR"]},
  {id:"f11", q:"Switch between base, upside and downside cases with one input cell", a:"CHOOSE (or INDEX) driven by a case number", o:["CHOOSE (or INDEX) driven by a case number","VLOOKUP on a hidden sheet","Copy the model three times","IF with 10 nested levels"]},
  {id:"f12", q:"Payment on a $1,000,000 loan, 7% annual rate, 10 years, monthly payments", a:"=PMT(7%/12,120,-1000000)", o:["=PMT(7%/12,120,-1000000)","=PMT(7%,10,1000000)","=PV(7%/12,120,1000000)","=RATE(120,7%,1000000)"]}
];

/* Numeric build drills. Numbers are illustrative, not any company's actuals.
   Answers are checked within the tolerance shown. */
window.EXCEL_CASE = {
  title: "Practice refiner (illustrative numbers, $ millions)",
  inputs: [
    ["Revenue", 100000], ["Cost of sales (excl. D&A)", 92000], ["Operating expenses", 2000],
    ["D&A", 2500], ["Interest expense", 600], ["Tax rate", "22%"], ["Capex", 2000],
    ["Increase in net working capital", 300], ["Total debt", 12000], ["Cash", 4000],
    ["Revenue growth (next 3 years)", "5% per year"], ["Discount rate (WACC)", "9%"]
  ]
};
window.EXCEL_DRILLS = [
  {id:"d1", q:"EBITDA", hint:"Revenue - cost of sales - operating expenses", ans:6000, tol:0.5, unit:"$m"},
  {id:"d2", q:"EBITDA margin", hint:"EBITDA / revenue", ans:6.0, tol:0.05, unit:"%"},
  {id:"d3", q:"EBIT", hint:"EBITDA - D&A", ans:3500, tol:0.5, unit:"$m"},
  {id:"d4", q:"Pre-tax income (EBT)", hint:"EBIT - interest", ans:2900, tol:0.5, unit:"$m"},
  {id:"d5", q:"Net income", hint:"EBT x (1 - 22%)", ans:2262, tol:0.5, unit:"$m"},
  {id:"d6", q:"NOPAT", hint:"EBIT x (1 - tax rate)", ans:2730, tol:0.5, unit:"$m"},
  {id:"d7", q:"Unlevered free cash flow", hint:"NOPAT + D&A - capex - increase in NWC", ans:2930, tol:0.5, unit:"$m"},
  {id:"d8", q:"Total debt / EBITDA", hint:"Leverage", ans:2.0, tol:0.01, unit:"x"},
  {id:"d9", q:"Net debt / EBITDA", hint:"(Debt - cash) / EBITDA", ans:1.33, tol:0.01, unit:"x"},
  {id:"d10", q:"EBITDA / interest", hint:"Coverage", ans:10.0, tol:0.01, unit:"x"},
  {id:"d11", q:"Revenue in year 3 at 5% growth", hint:"=100000*(1+5%)^3", ans:115762.5, tol:1, unit:"$m"},
  {id:"d12", q:"Year-3 discount factor at 9% (end of year)", hint:"=1/(1+9%)^3", ans:0.7722, tol:0.0005, unit:""},
  {id:"d13", q:"Present value of $1,000 received at the end of year 3 at 9%", hint:"=1000/(1.09)^3", ans:772.18, tol:0.5, unit:"$m"},
  {id:"d14", q:"Terminal value if next year's FCF is $3,000, WACC 9%, growth 2%", hint:"=3000/(9%-2%)", ans:42857.14, tol:1, unit:"$m"},
  {id:"d15", q:"Implied EV at 7.0x EBITDA", hint:"=6000*7", ans:42000, tol:0.5, unit:"$m"},
  {id:"d16", q:"Implied equity value at 7.0x EBITDA", hint:"EV - debt + cash", ans:34000, tol:0.5, unit:"$m"}
];
