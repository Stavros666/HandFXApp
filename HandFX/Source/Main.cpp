#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_gui_extra/juce_gui_extra.h>   
#include "MainComponent.h"

class HandFXApplication : public juce::JUCEApplication
{
public:
    const juce::String getApplicationName() override    { return "HandFX"; }
    const juce::String getApplicationVersion() override { return "0.1"; }
    bool moreThanOneInstanceAllowed() override          { return true; }

    void initialise (const juce::String&) override
    {
        mainWindow = std::make_unique<MainWindow>(getApplicationName());
    }

    void shutdown() override { mainWindow.reset(); }

private:
    class MainWindow : public juce::DocumentWindow
    {
    public:
        MainWindow (juce::String name)
            : juce::DocumentWindow(
                name,
                juce::Desktop::getInstance().getDefaultLookAndFeel()
                    .findColour(juce::ResizableWindow::backgroundColourId),
                juce::DocumentWindow::allButtons)
        {
            setUsingNativeTitleBar(true);
            setContentOwned(new MainComponent(), true);
            centreWithSize(800, 600);
            setResizable(true, true);
            setVisible(true);
        }

        void closeButtonPressed() override
        {
            if (auto* app = juce::JUCEApplication::getInstance())
                app->systemRequestedQuit();
        }
    };

    std::unique_ptr<MainWindow> mainWindow;
};

START_JUCE_APPLICATION(HandFXApplication)
