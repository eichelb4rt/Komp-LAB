import numpy as np
import numpy.typing as npt
from dag_search.eliminations import EliminationRegressor
from dag_search import dag_search
import matplotlib.pyplot as plt
plt.rcParams["figure.dpi"] = 300


def main():
    x: npt.NDArray[np.int32]
    y: npt.NDArray[np.int32]
    x, y = np.load("runtimes/runtime_task2a_compressed.npy")
    x = x[:, np.newaxis]
    estimator = EliminationRegressor(dag_search.DAGRegressorPoly())
    estimator.fit(x, y)
    formula = estimator.model()
    print(formula)
    plt.scatter(x, y, label="runtimes", s=0.2)
    plt.plot(x, estimator.predict(x), label=str(formula), color="red", linewidth=0.5)
    plt.legend()
    plt.savefig("plots/prediction_task2a.png")
    
    
    

if __name__ == "__main__":
    main()
