#pragma once
#include <juce_gui_basics/juce_gui_basics.h>

class MainComponent : public juce::Component
{
public:
    MainComponent();
    void resized() override;

private:
    juce::TextButton helloButton;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MainComponent)
};
