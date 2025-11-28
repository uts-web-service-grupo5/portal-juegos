from sqlalchemy.orm import Session

from app.catalog_database import GameDB


class CatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_games(self) -> list[GameDB]:
        return self.db.query(GameDB).all()

    def get_games_for(self, plan: str, edad: int) -> list[GameDB]:
        games = self.list_games()
        plan_upper = plan.capitalize()
        result = []
        for g in games:
            planes = [p.strip() for p in g.acceso_plan.split(",")]
            if plan_upper in planes and edad >= g.restriccion_edad:
                result.append(g)
        return result

    def get_by_id(self, game_id: int) -> GameDB | None:
        return self.db.query(GameDB).filter(GameDB.id == game_id).first()
