declare module 'jstat' {
    export const jStat: {
        normal: {
            cdf(x: number, mean: number, std: number): number;
        };
        anovaftest(...args: number[][]): number;
        centralF: {
            cdf(x: number, df1: number, df2: number): number;
        };
        corrcoeff(x: number[], y: number[]): number;
        studentt: {
            cdf(x: number, df: number): number;
        };
        chisquare: {
            cdf(x: number, df: number): number;
        };
        beta: {
            cdf(x: number, alpha: number, beta: number): number;
            inv(p: number, alpha: number, beta: number): number;
        };
    };
}
