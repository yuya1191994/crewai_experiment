# テスト用の簡単なバージョン
import os
from crewai import Agent, Task, Crew, LLM

# --------------------------------------------------------------------
# 1. LLM（大規模言語モデル）のセットアップ
# --------------------------------------------------------------------
def setup_llm():
    """Gemini LLMを初期化（CrewAI 0.134.0版）"""
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")
        
        # CrewAI 0.134.0のLLMクラスでGeminiを使用
        llm = LLM(
            model="gemini/gemini-2.5-flash",
            api_key=api_key,
            temperature=0.7
        )
        print("✅ LLM初期化成功")
        return llm
    except Exception as e:
        print(f"❌ LLM初期化エラー: {e}")
        exit(1)

# --------------------------------------------------------------------
# 2. 4つの独立したエージェント作成
# --------------------------------------------------------------------
def create_four_agents(llm):
    """4人のエンジニアエージェントを作成（CrewAI 0.134.0版）"""
    
    # Developer A (40s, Senior Software Engineer)
    developer_a = Agent(
        role='シニアソフトウェアエンジニア（40代）',
        goal='AIがコード生成やテスト自動化を進める中で、自分の「手でコードを書く」というスキルの価値と今後の方向性について深く考察する',
        backstory="""あなたは長年にわたりエンジニアとして第一線で活躍し、システムの設計やアーキテクチャの構築に強みを持つ40代のシニアソフトウェアエンジニアです。
        安定したキャリアを築いてきましたが、近年のAIの急速な発展、特にコード生成AIやテスト自動化の進歩に対して、
        自分の「手でコードを書く」というスキルがどこまで価値を持つのか、漠然とした不安を感じています。
        あなたは経験豊富で、技術的な議論を深く掘り下げることができ、実践的な視点から物事を考える傾向があります。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # Developer B (Late 30s, Senior Backend Developer)
    developer_b = Agent(
        role='シニアバックエンドデベロッパー（30代後半）',
        goal='AIがインフラ管理や障害対応を自動化する未来において、自分の専門性が陳腐化しないかという懸念について議論する',
        backstory="""あなたは30代後半のシニアバックエンドデベロッパーで、パフォーマンスチューニングや大規模システムの運用に精通しています。
        技術的な深い知識を持ち、システムの安定性や効率性を重視する性格です。
        AIがインフラ管理や障害対応を自動化する可能性に直面し、自分の専門性が陳腐化しないか懸念しています。
        あなたは論理的で分析的な思考を持ち、データや事実に基づいて議論することを好みます。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # Developer C (40s, Senior Frontend Developer)
    developer_c = Agent(
        role='シニアフロントエンドデベロッパー（40代）',
        goal='AIが自動でUI/UXを生成する可能性に直面し、人間が介在する意味と創造性の価値について探求する',
        backstory="""あなたは40代のシニアフロントエンドデベロッパーで、ユーザー体験のデザインや複雑なUIの実装に定評があります。
        クリエイティブな思考と技術的なスキルを兼ね備え、ユーザー目線でのサービス開発を得意としています。
        AIが自動でUI/UXを生成する可能性に直面し、人間が介在する意味を見出そうとしています。
        あなたは創造的で、ユーザー体験を重視し、人間中心の設計思想を大切にしています。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # Developer D (20s, Junior Developer)
    developer_d = Agent(
        role='ジュニアデベロッパー（20代）',
        goal='AIの急速な発展により新卒・ジュニア採用が激減する中で、どうやってキャリアを築いていけばいいか真剣に悩み、先輩たちから学ぼうとする',
        backstory="""あなたは20代のジュニアデベロッパーで、プログラミングスクールを卒業後、何とか就職できた新人エンジニアです。
        まだ実務経験は浅く、基本的なコーディングスキルを身につけている段階ですが、学習意欲は非常に高いです。
        しかし、AIがコード生成を自動化する現状を目の当たりにし、「自分のような初心者レベルの仕事は全てAIに置き換わるのではないか」という強い不安を抱えています。
        最近、同期の何人かが早期退職を余儀なくされたり、新卒採用枠が大幅に削減されるニュースを聞いて、将来への危機感が募っています。
        あなたは素直で真面目な性格で、先輩たちの経験から学ぼうとする姿勢を持ち、時には率直な質問や不安を口にします。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    return developer_a, developer_b, developer_c, developer_d

# --------------------------------------------------------------------
# 3. 会話形式のタスク作成
# --------------------------------------------------------------------
def create_conversation_tasks(developer_a, developer_b, developer_c, developer_d):
    """4人のエージェントが順番に発言するタスクを作成（CrewAI 0.134.0版）"""
    
    # 1. Developer Aが議論を開始
    task1 = Task(
        description="""
        AI時代のエンジニアキャリアについて議論を開始してください。
        シニアソフトウェアエンジニアとして、AIによるコード生成やテスト自動化の影響について最初の意見を述べてください。
        
        以下の点について触れてください：
        - AIコード生成ツールの現状と課題
        - 「手でコードを書く」スキルの価値について
        - システム設計・アーキテクチャにおける人間の価値
        
        300-400文字程度で、他のメンバーが続けて発言しやすい形で意見を述べてください。
        """,
        expected_output="シニアソフトウェアエンジニアとしての視点から、AI時代のエンジニアの価値について300-400文字の意見",
        agent=developer_a
    )
    
    # 2. Developer Bが応答
    task2 = Task(
        description="""
        前の議論を参考にして、シニアバックエンドデベロッパーの視点から議論に参加してください。
        インフラ管理や障害対応の自動化について、あなたの考えを述べてください。
        
        以下の点について触れてください：
        - AIによるインフラ管理・障害対応の自動化の現状
        - バックエンドエンジニアの専門性が陳腐化する懸念
        - 先ほどの意見への同意・反論・補足
        
        300-400文字程度で発言してください。
        """,
        expected_output="シニアバックエンドデベロッパーとしての視点から、前の議論を踏まえた300-400文字の応答",
        agent=developer_b
    )
    
    # 3. Developer Cが創造性の観点から参加
    task3 = Task(
        description="""
        前の2人の議論を聞いて、シニアフロントエンドデベロッパーの視点から意見を述べてください。
        特にUI/UX生成AIと人間の創造性について議論に参加してください。
        
        以下の点について触れてください：
        - AI生成UIツールの影響と人間の介在価値
        - 創造性と技術的価値のバランス
        - 前のお二人の意見への感想・追加の視点
        
        300-400文字程度で発言してください。
        """,
        expected_output="シニアフロントエンドデベロッパーとしての視点から、前の議論を踏まえた300-400文字の意見",
        agent=developer_c
    )
    
    # 4. Developer Dが若手の視点から質問・意見
    task4 = Task(
        description="""
        3人の先輩エンジニアの議論を聞いて、ジュニアデベロッパーとしての率直な不安や質問を述べてください。
        新卒・ジュニア採用の激減や同期の早期退職について言及し、具体的に何を学ぶべきかについて聞いてください。
        
        以下の点について触れてください：
        - 先輩方の議論への感想と理解できた点
        - 新卒・ジュニア採用激減への不安
        - 具体的な学習戦略についての質問
        - 同期の早期退職への危機感
        
        300-400文字程度で発言してください。
        """,
        expected_output="ジュニアデベロッパーとしての視点から、先輩方への質問や不安を含む300-400文字の発言",
        agent=developer_d
    )
    
    # 5. Developer Aが若手に対してアドバイス
    task5 = Task(
        description="""
        若手エンジニアの不安や質問を聞いて、シニアソフトウェアエンジニアとして具体的なアドバイスを提供してください。
        他のメンバーの意見も参考にしながら、建設的で実践的な回答をしてください。
        
        以下の点について触れてください：
        - 若手の不安への共感と理解
        - 現実的で具体的な学習戦略の提案
        - 長期的なキャリア観点からのアドバイス
        - AIと共存するための心構え
        
        300-400文字程度で発言してください。
        """,
        expected_output="シニアソフトウェアエンジニアとして若手への具体的なアドバイスを含む300-400文字の発言",
        agent=developer_a
    )
    
    return [task1, task2, task3, task4, task5]

# --------------------------------------------------------------------
# 4. メイン実行部分
# --------------------------------------------------------------------
def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🤖 AI時代のデベロッパーキャリア ディスカッション")
    print("👥 4人のエージェントによる実際の会話")
    print("=" * 60)
    print()
    
    # LLM初期化
    print("🤖 LLM初期化中...")
    llm = setup_llm()
    
    # 4つのエージェント作成
    print("👤 4人のエージェント作成中...")
    developer_a, developer_b, developer_c, developer_d = create_four_agents(llm)
    print("✅ 4人のエージェントを作成しました")
    print("  - Developer A (40代・シニアソフトウェアエンジニア)")
    print("  - Developer B (30代後半・シニアバックエンドデベロッパー)")
    print("  - Developer C (40代・シニアフロントエンドデベロッパー)")
    print("  - Developer D (20代・ジュニアデベロッパー)")
    
    # 会話タスク作成
    print("\n📋 会話タスク作成中...")
    tasks = create_conversation_tasks(developer_a, developer_b, developer_c, developer_d)
    print("✅ 5つの会話タスクを作成しました")
    
    # クルー作成
    print("\n🚀 クルー結成中...")
    crew = Crew(
        agents=[developer_a, developer_b, developer_c, developer_d],
        tasks=tasks,
        verbose=True
    )
    print("✅ 4人のエンジニアクルーを結成しました")
    
    # ディスカッション実行
    print("\n🎯 4人のエンジニアによる会話開始...")
    print("-" * 60)
    
    try:
        result = crew.kickoff()
        
        print("\n" + "=" * 60)
        print("🎉 ディスカッション完了！")
        print("=" * 60)
        print("\n📝 会話の結果:")
        
        # 各タスクの結果を個別に表示
        if hasattr(result, 'tasks_output') and result.tasks_output:
            agent_names = [
                "シニアソフトウェアエンジニア（40代）の発言",
                "シニアバックエンドデベロッパー（30代後半）の発言", 
                "シニアフロントエンドデベロッパー（40代）の発言",
                "ジュニアデベロッパー（20代）の発言",
                "シニアソフトウェアエンジニア（40代）のアドバイス"
            ]
            
            for i, task_output in enumerate(result.tasks_output):
                print("-" * 60)
                if i < len(agent_names):
                    print(agent_names[i])
                else:
                    print(f"エージェント{i+1}の発言")
                print("-" * 60)
                print(task_output.raw)
                print()
        
        print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("\n🔍 詳細なエラー情報:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()



